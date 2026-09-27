import hashlib
import io
import uuid
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.core.exceptions import ModelOpsException, NotFoundException
from apps.api.app.infrastructure.database.models import Dataset, DatasetValidationReport, DatasetVersion
from apps.api.app.infrastructure.storage import get_storage_service
from apps.api.app.modules.datasets.schemas import (
    DatasetDetailResponse,
    DatasetPreviewResponse,
    DatasetSummary,
    DatasetVersionDetail,
    ValidationReportResponse,
)
from ml.pipelines.validation.validator import validate_churn_dataset

class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = get_storage_service()

    async def create_dataset_with_file(
        self,
        workspace_id: str,
        name: str,
        file_bytes: bytes,
        filename: str,
        description: Optional[str] = None,
        domain: str = "churn",
        target_column: str = "Churn",
    ) -> DatasetDetailResponse:
        # 1. Verify CSV and calculate hash
        checksum = hashlib.sha256(file_bytes).hexdigest()

        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception as e:
            raise ModelOpsException(f"Failed to parse CSV file: {str(e)}")

        row_count = len(df)
        col_count = len(df.columns)

        # 2. Schema Validation
        is_valid, val_report = validate_churn_dataset(df, target_column=target_column)

        # 3. Create Dataset Record
        dataset = Dataset(
            workspace_id=workspace_id,
            name=name,
            description=description,
            domain=domain,
            target_column=target_column,
        )
        self.db.add(dataset)
        await self.db.flush()

        # 4. Upload raw CSV to Storage Service
        destination_path = f"datasets/{workspace_id}/{dataset.id}/v1_{filename}"
        await self.storage.upload_file(
            file_obj=io.BytesIO(file_bytes),
            destination_path=destination_path,
            content_type="text/csv",
        )

        # 5. Create Dataset Version
        schema_metadata = {
            "columns": list(df.columns),
            "dtypes": {k: str(v) for k, v in df.dtypes.items()},
            "shape": [row_count, col_count],
        }

        version = DatasetVersion(
            dataset_id=dataset.id,
            version_number=1,
            file_path=destination_path,
            file_size_bytes=len(file_bytes),
            checksum_sha256=checksum,
            row_count=row_count,
            column_count=col_count,
            schema_metadata=schema_metadata,
            is_validated=is_valid,
        )
        self.db.add(version)
        await self.db.flush()

        # 6. Save Validation Report
        report_record = DatasetValidationReport(
            dataset_version_id=version.id,
            status=val_report["status"],
            missing_value_summary=val_report.get("missing_value_summary", {}),
            class_balance_summary=val_report.get("class_balance_summary", {}),
            column_checks=val_report.get("column_checks", []),
            errors=val_report.get("errors", []),
            warnings=val_report.get("warnings", []),
        )
        self.db.add(report_record)
        await self.db.commit()

        return await self.get_dataset(workspace_id, dataset.id)

    async def list_datasets(self, workspace_id: str) -> List[DatasetSummary]:
        stmt = (
            select(Dataset)
            .options(
                selectinload(Dataset.versions).selectinload(DatasetVersion.validation_report)
            )
            .where(Dataset.workspace_id == workspace_id)
            .order_by(desc(Dataset.created_at))
        )
        res = await self.db.execute(stmt)
        datasets = res.scalars().all()

        summaries = []
        for ds in datasets:
            latest_v = ds.versions[-1] if ds.versions else None
            status = latest_v.validation_report.status if latest_v and latest_v.validation_report else "UNKNOWN"
            summaries.append(
                DatasetSummary(
                    id=ds.id,
                    name=ds.name,
                    description=ds.description,
                    domain=ds.domain,
                    target_column=ds.target_column,
                    created_at=ds.created_at.isoformat(),
                    latest_version=latest_v.version_number if latest_v else None,
                    total_rows=latest_v.row_count if latest_v else 0,
                    total_columns=latest_v.column_count if latest_v else 0,
                    status=status,
                )
            )
        return summaries

    async def get_dataset(self, workspace_id: str, dataset_id: str) -> DatasetDetailResponse:
        stmt = (
            select(Dataset)
            .options(
                selectinload(Dataset.versions).selectinload(DatasetVersion.validation_report)
            )
            .where(
                Dataset.id == dataset_id,
                Dataset.workspace_id == workspace_id,
            )
        )
        res = await self.db.execute(stmt)
        ds = res.scalar_one_or_none()
        if not ds:
            raise NotFoundException("Dataset", dataset_id)

        version_details = [
            DatasetVersionDetail(
                id=v.id,
                version_number=v.version_number,
                file_size_bytes=v.file_size_bytes,
                checksum_sha256=v.checksum_sha256,
                row_count=v.row_count,
                column_count=v.column_count,
                schema_metadata=v.schema_metadata,
                is_validated=v.is_validated,
                created_at=v.created_at.isoformat(),
            )
            for v in ds.versions
        ]

        latest_validation = None
        if ds.versions and ds.versions[-1].validation_report:
            vr = ds.versions[-1].validation_report
            latest_validation = ValidationReportResponse(
                id=vr.id,
                dataset_version_id=vr.dataset_version_id,
                status=vr.status,
                is_valid=(vr.status in ["PASSED", "WARNINGS"]),
                missing_value_summary=vr.missing_value_summary,
                class_balance_summary=vr.class_balance_summary,
                column_checks=vr.column_checks,
                errors=vr.errors,
                warnings=vr.warnings,
                created_at=vr.created_at.isoformat(),
            )

        return DatasetDetailResponse(
            id=ds.id,
            name=ds.name,
            description=ds.description,
            domain=ds.domain,
            target_column=ds.target_column,
            created_at=ds.created_at.isoformat(),
            versions=version_details,
            latest_validation=latest_validation,
        )

    async def get_dataset_preview(
        self, workspace_id: str, dataset_id: str, page: int = 1, page_size: int = 20
    ) -> DatasetPreviewResponse:
        ds = await self.get_dataset(workspace_id, dataset_id)
        if not ds.versions:
            return DatasetPreviewResponse(columns=[], rows=[], total_rows=0, page=page, page_size=page_size)

        latest_v = ds.versions[-1]
        # Fetch file from storage
        file_bytes = await self.storage.download_file(
            f"datasets/{workspace_id}/{dataset_id}/v{latest_v.version_number}"
        ) if await self.storage.file_exists(
            f"datasets/{workspace_id}/{dataset_id}/v{latest_v.version_number}"
        ) else None

        # If key pattern was filename based, query the actual DB model
        if not file_bytes:
            v_res = await self.db.execute(select(DatasetVersion).where(DatasetVersion.id == latest_v.id))
            version_obj = v_res.scalar_one_or_none()
            if version_obj:
                file_bytes = await self.storage.download_file(version_obj.file_path)

        if not file_bytes:
            raise NotFoundException("Dataset file", dataset_id)

        df = pd.read_csv(io.BytesIO(file_bytes))
        total_rows = len(df)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paged_df = df.iloc[start_idx:end_idx]

        # Convert nan to None for valid JSON serialization
        clean_records = paged_df.fillna("").to_dict(orient="records")

        return DatasetPreviewResponse(
            columns=list(df.columns),
            rows=clean_records,
            total_rows=total_rows,
            page=page,
            page_size=page_size,
        )
