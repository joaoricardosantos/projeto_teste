from typing import List
from ninja import Router, Schema
from ninja.errors import HttpError
from core.models import User
from core.auth import JWTAuth
from pydantic import UUID4, EmailStr

admin_router = Router(auth=JWTAuth())


class UserApprovalIn(Schema):
    user_id: UUID4
    is_approved: bool


class UserCreateIn(Schema):
    name: str
    email: EmailStr
    password: str


class UserOut(Schema):
    id: UUID4
    name: str
    email: str
    is_approved: bool
    is_active: bool


@admin_router.get("/users", response=List[UserOut])
def list_users(request):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    return User.objects.all().order_by("-created_at")


@admin_router.post("/approve-user", response={200: dict})
def approve_user(request, payload: UserApprovalIn):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        user = User.objects.get(id=payload.user_id)
        user.is_approved = payload.is_approved
        user.save()
        return 200, {"message": "User_approval_status_updated"}
    except User.DoesNotExist:
        raise HttpError(404, "User_not_found")


@admin_router.post("/create-user", response={201: dict})
def create_user(request, payload: UserCreateIn):
    """
    Criação de usuários restrita a administradores autenticados.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "Email_already_registered")

    User.objects.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )

    return 201, {"message": "User_created_successfully_pending_approval"}