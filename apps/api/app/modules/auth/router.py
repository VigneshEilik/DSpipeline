from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import get_current_user
from apps.api.app.infrastructure.database.models import User
from apps.api.app.infrastructure.database.session import get_db
from apps.api.app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
)
from apps.api.app.modules.auth.service import AuthService
from apps.api.app.shared.schemas.common import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, token_data = await service.register(req)

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS production
        max_age=token_data.expires_in,
    )

    return APIResponse(data=token_data, message="Account created successfully.")

@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user, token_data = await service.login(req)

    # Set secure HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token_data.access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=token_data.expires_in,
    )

    return APIResponse(data=token_data, message="Login successful.")

@router.post("/logout", response_model=APIResponse[dict])
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return APIResponse(data={"logged_out": True}, message="Successfully logged out.")

@router.get("/me", response_model=APIResponse[UserProfileResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    profile = await service.get_user_profile(current_user.id)
    return APIResponse(data=profile)

@router.post("/bootstrap-dev", response_model=APIResponse[TokenResponse])
async def bootstrap_dev_user(db: AsyncSession = Depends(get_db)):
    """
    Development-only bootstrap endpoint to guarantee a test user exists.
    """
    service = AuthService(db)
    req = RegisterRequest(
        email="dev@modelops.local",
        password="ModelOpsPassword123!",
        full_name="Lead Data Scientist",
        workspace_name="Acme Churn Intelligence",
    )
    try:
        user, token_data = await service.register(req)
        return APIResponse(data=token_data, message="Development user bootstrapped.")
    except Exception:
        # If already bootstrapped, log in
        login_req = LoginRequest(email="dev@modelops.local", password="ModelOpsPassword123!")
        user, token_data = await service.login(login_req)
        return APIResponse(data=token_data, message="Development user authenticated.")
