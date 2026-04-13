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
    is_juridico = models.BooleanField(default=False)
    is_financeiro = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return self.email


class MessageTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    body = models.TextField(help_text='Use {nome}, {unidade}, {condominio}, {valor}, {vencimento}, {data_atraso}, {qtd} como variáveis.')
    is_active = models.BooleanField(default=True) 
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

class SheetSetor(models.Model):
    TIPO_CHOICES = [
        ('cobrancas', 'Cobranças / Vencimentos'),
        ('advocacia', 'Honorários Advocatícios'),
        ('despesas', 'Despesas por Unidade'),
        ('financeiro', 'Financeiro'),
        ('fluxo_caixa', 'Fluxo de Caixa'),
    ]

    nome = models.CharField(max_length=100)
    spreadsheet_id = models.CharField(max_length=200)
    aba = models.CharField(max_length=100, default='Sheet1')
    tipo_dashboard = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cobrancas')
    grupo = models.CharField(max_length=100, blank=True, default='', help_text='Grupo/categoria para agrupar setores (ex: Financeiro, Jurídico)')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criado_em']
        verbose_name = 'Setor Planilha'
        verbose_name_plural = 'Setores Planilha'

    def __str__(self):
        return self.nome


class DespesaLocal(models.Model):
    """Despesas e custos cadastrados manualmente no sistema."""

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago',     'Pago'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    condominio_id   = models.IntegerField()
    condominio_nome = models.CharField(max_length=255, blank=True)
    descricao       = models.CharField(max_length=500)
    fornecedor      = models.CharField(max_length=255, blank=True)
    categoria       = models.CharField(max_length=255, blank=True)
    valor           = models.DecimalField(max_digits=14, decimal_places=2)
    vencimento      = models.DateField()
    data_pagamento  = models.DateField(null=True, blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacao      = models.TextField(blank=True)
    criado_por      = models.CharField(max_length=255, blank=True)
    criado_em       = models.DateTimeField(auto_now_add=True)
    atualizado_em   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Despesa Local"
        verbose_name_plural = "Despesas Locais"
        ordering = ["-vencimento"]

    def __str__(self):
        return f"{self.descricao} — R$ {self.valor} ({self.status})"


class AgendaTarefa(models.Model):
    """Tarefas do calendário de agenda."""
    COR_CHOICES = [
        ('primary', 'Azul'),
        ('success', 'Verde'),
        ('error',   'Vermelho'),
        ('warning', 'Laranja'),
        ('info',    'Ciano'),
    ]
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo        = models.CharField(max_length=255)
    descricao     = models.TextField(blank=True)
    data          = models.DateField()
    hora          = models.TimeField(null=True, blank=True)
    cor           = models.CharField(max_length=20, choices=COR_CHOICES, default='primary')
    checklist     = models.JSONField(default=list, blank=True)
    criado_por    = models.CharField(max_length=255, blank=True)
    criado_em     = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['data', 'hora']
        verbose_name = 'Tarefa de Agenda'
        verbose_name_plural = 'Tarefas de Agenda'

    def __str__(self):
        return f"{self.data} — {self.titulo}"


class CondominioIdValido(models.Model):
    """
    Cache dos IDs de condomínio que realmente existem na Superlógica.
    Evita varrer IDs inexistentes a cada consulta do dashboard.
    """
    id_condominio  = models.IntegerField(unique=True)
    nome           = models.CharField(max_length=255, blank=True)
    atualizado_em  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id_condominio']
        verbose_name = 'ID de Condomínio Válido'
        verbose_name_plural = 'IDs de Condomínios Válidos'

    def __str__(self):
        return f"#{self.id_condominio} {self.nome}"


class InadimplenciaSnapshot(models.Model):
    """
    Snapshot mensal do total de inadimplência (Superlógica).
    Salvo automaticamente a cada geração do dashboard.
    Apenas um registro por mês (ano + mês).
    """
    ano        = models.PositiveSmallIntegerField()
    mes        = models.PositiveSmallIntegerField()       # 1-12
    total      = models.DecimalField(max_digits=16, decimal_places=2)
    capturado_em = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('ano', 'mes')
        ordering = ['ano', 'mes']
        verbose_name = 'Snapshot de Inadimplência'
        verbose_name_plural = 'Snapshots de Inadimplência'

    def __str__(self):
        return f"{self.mes:02d}/{self.ano} — R$ {self.total}"


class DespesaParaPagar(models.Model):
    """Despesas do Superlógica marcadas para pagamento pelo financeiro."""

    STATUS_CHOICES = [
        ('aguardando', 'Aguardando Pagamento'),
        ('pago',       'Pago'),
        ('cancelado',  'Cancelado'),
    ]

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_despesa      = models.CharField(max_length=64)
    id_parcela      = models.CharField(max_length=64, blank=True)
    id_contato      = models.CharField(max_length=64, blank=True)
    descricao       = models.CharField(max_length=500)
    fornecedor      = models.CharField(max_length=255, blank=True)
    condominio_id   = models.IntegerField()
    condominio_nome = models.CharField(max_length=255, blank=True)
    valor           = models.DecimalField(max_digits=14, decimal_places=2)
    vencimento      = models.CharField(max_length=10, blank=True)   # DD/MM/YYYY
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aguardando')
    observacao      = models.TextField(blank=True)
    marcado_por     = models.CharField(max_length=255, blank=True)
    marcado_em      = models.DateTimeField(auto_now_add=True)
    atualizado_em   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['marcado_em']
        verbose_name = 'Despesa Para Pagar'
        verbose_name_plural = 'Despesas Para Pagar'

    def __str__(self):
        return f"{self.descricao} — R$ {self.valor} ({self.status})"


class ResponsavelPeticao(models.Model):
    """Perfis de responsável pela petição para uso nos documentos de execução."""
    nome     = models.CharField(max_length=255)
    funcao   = models.CharField(max_length=255, blank=True, default="")
    padrao   = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Responsável pela Petição"
        ordering = ["-padrao", "nome"]

    def __str__(self):
        return f"{self.nome} ({self.funcao})"


class AdvogadoPlanilha(models.Model):
    """Advogado vinculado a uma planilha Google Sheets para a aba Jurídico."""
    nome = models.CharField(max_length=255)
    spreadsheet_id = models.CharField(max_length=200)
    aba = models.CharField(max_length=100, blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Advogado Planilha'
        verbose_name_plural = 'Advogados Planilhas'

    def __str__(self):
        return self.nome


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
