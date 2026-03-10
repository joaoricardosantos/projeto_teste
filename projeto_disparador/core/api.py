from ninja import Router
from django.contrib.auth import authenticate
from core.models import User
from core.schemas import RegisterIn, LoginIn, TokenOut
from core.security import create_access_token
from ninja.errors import HttpError

auth_router = Router()

@auth_router.post("/register", response={201: dict})
def register(request, payload: RegisterIn):
    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "Email_already_registered")
    
    User.objects.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name
    )
    return 201, {"message": "Registration_successful_pending_approval"}

@auth_router.post("/login", response=TokenOut)
def login(request, payload: LoginIn):
    user = authenticate(request, email=payload.email, password=payload.password)
    
    if not user:
        raise HttpError(401, "Invalid_credentials")
    
    if not user.is_approved:
        raise HttpError(403, "Account_pending_approval")
        
    if not user.is_active:
        raise HttpError(403, "Account_disabled")
    
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}