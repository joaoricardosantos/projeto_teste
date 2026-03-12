import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageTemplate",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=120, verbose_name="Nome do template")),
                (
                    "body",
                    models.TextField(
                        verbose_name="Corpo da mensagem",
                        help_text=(
                            "Variáveis disponíveis: {nome}, {condominio}, {valor}, {data_atraso}"
                        ),
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=False,
                        verbose_name="Template ativo",
                        help_text="Apenas um template pode estar ativo por vez.",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Criado em"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]