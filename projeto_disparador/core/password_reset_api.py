from ninja import Router, Schema
from ninja.errors import HttpError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from core.models import User, PasswordResetToken
import secrets

password_router = Router()


class ForgotPasswordIn(Schema):
    email: str


class ResetPasswordIn(Schema):
    token: str
    new_password: str


@password_router.post("/forgot-password", response={200: dict})
def forgot_password(request, payload: ForgotPasswordIn):
    """
    Gera um token de reset e envia por e-mail.
    Sempre retorna 200 para não revelar se o e-mail existe.
    """
    try:
        user = User.objects.get(email=payload.email)
    except User.DoesNotExist:
        # Retorna 200 mesmo assim para não vazar informação
        return 200, {"message": "If_email_exists_reset_link_sent"}

    # Invalida tokens anteriores do usuário
    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

    # Cria novo token
    token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(user=user, token=token)

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    send_mail(
        subject="Redefinição de senha — Sistema de Inadimplentes",
        message=(
            f"Olá, {user.name}!\n\n"
            f"Recebemos uma solicitação para redefinir a senha da sua conta.\n\n"
            f"Clique no link abaixo para criar uma nova senha:\n{reset_url}\n\n"
            f"Este link expira em 1 hora.\n\n"
            f"Se você não solicitou a redefinição, ignore este e-mail."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    return 200, {"message": "If_email_exists_reset_link_sent"}


@password_router.post("/reset-password", response={200: dict})
def reset_password(request, payload: ResetPasswordIn):
    """
    Valida o token e redefine a senha do usuário.
    """
    try:
        reset_token = PasswordResetToken.objects.select_related("user").get(
            token=payload.token,
            used=False,
        )
    except PasswordResetToken.DoesNotExist:
        raise HttpError(400, "Invalid_or_expired_token")

    # Verifica expiração (1 hora)
    age = timezone.now() - reset_token.created_at
    if age.total_seconds() > 3600:
        reset_token.used = True
        reset_token.save()
        raise HttpError(400, "Invalid_or_expired_token")

    user = reset_token.user
    user.set_password(payload.new_password)
    user.save()

    reset_token.used = True
    reset_token.save()

    return 200, {"message": "Password_reset_successfully"}