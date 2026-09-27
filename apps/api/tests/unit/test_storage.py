import io
import pytest
from apps.api.app.infrastructure.storage.local import LocalStorageService

@pytest.mark.asyncio
async def test_local_storage_lifecycle(tmp_path):
    storage = LocalStorageService(base_dir=str(tmp_path))
    test_content = b"test dataset file content for customer churn"
    test_file = io.BytesIO(test_content)
    destination = "datasets/v1/telco_sample.csv"

    # Upload
    stored_path = await storage.upload_file(test_file, destination)
    assert destination in stored_path

    # Exists
    exists = await storage.file_exists(destination)
    assert exists is True

    # Download
    downloaded = await storage.download_file(destination)
    assert downloaded == test_content

    # Delete
    deleted = await storage.delete_file(destination)
    assert deleted is True

    # Exists after deletion
    exists_after = await storage.file_exists(destination)
    assert exists_after is False

@pytest.mark.asyncio
async def test_local_storage_path_traversal_prevention(tmp_path):
    storage = LocalStorageService(base_dir=str(tmp_path))
    with pytest.raises(ValueError, match="Path traversal detected"):
        storage._resolve_path("../../etc/passwd")
