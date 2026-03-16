from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_approved", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_approved", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email


class MessageTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, verbose_name="Nome")
    body = models.TextField(verbose_name="Corpo da mensagem")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Template de mensagem"
        verbose_name_plural = "Templates de mensagem"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Campanha(models.Model):
    """Representa um disparo em massa (upload de Excel)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255, verbose_name="Nome da campanha")
    criada_em = models.DateTimeField(default=timezone.now)
    total_enviados = models.IntegerField(default=0)
    total_erros = models.IntegerField(default=0)
    total_sem_numero = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Campanha"
        verbose_name_plural = "Campanhas"
        ordering = ["-criada_em"]

    def __str__(self):
        return f"{self.nome} ({self.criada_em.strftime('%d/%m/%Y %H:%M')})"


class MensagemEnviada(models.Model):
    """Registra cada mensagem enviada individualmente."""

    STATUS_ENVIADO    = "enviado"
    STATUS_RESPONDIDO = "respondido"
    STATUS_ERRO       = "erro"

    STATUS_CHOICES = [
        (STATUS_ENVIADO,    "Enviado"),
        (STATUS_RESPONDIDO, "Respondido"),
        (STATUS_ERRO,       "Erro"),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campanha    = models.ForeignKey(Campanha, on_delete=models.CASCADE, related_name="mensagens")
    condominio  = models.CharField(max_length=512, blank=True)
    unidade     = models.CharField(max_length=255, blank=True)
    nome        = models.CharField(max_length=512, blank=True)
    telefone    = models.CharField(max_length=30)
    mensagem    = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ENVIADO)
    enviada_em  = models.DateTimeField(default=timezone.now)
    respondida_em = models.DateTimeField(null=True, blank=True)
    resposta    = models.TextField(blank=True)

    class Meta:
        verbose_name = "Mensagem enviada"
        verbose_name_plural = "Mensagens enviadas"
        ordering = ["-enviada_em"]
        indexes = [
            models.Index(fields=["telefone"]),
            models.Index(fields=["campanha", "status"]),
        ]

    def __str__(self):
        return f"{self.telefone} — {self.status}"

class PasswordResetToken(models.Model):
    """Token de redefinição de senha com expiração de 1 hora."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token      = models.CharField(max_length=128, unique=True, db_index=True)
    used       = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Token de reset de senha"

    def __str__(self):
        return f"Reset token para {self.user.email}"
