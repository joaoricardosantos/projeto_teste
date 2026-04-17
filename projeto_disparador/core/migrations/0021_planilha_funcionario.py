import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_advogadoplanilha'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanilhaFuncionarioConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('funcionario', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='planilha_config',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Config de Planilha do Funcionário',
                'ordering': ['funcionario__name'],
            },
        ),
        migrations.CreateModel(
            name='PlanilhaConfigColuna',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=200)),
                ('tipo', models.CharField(
                    choices=[('data', 'Data'), ('booleano', 'Booleano'), ('texto', 'Texto')],
                    default='texto',
                    max_length=20,
                )),
                ('ordem', models.IntegerField(default=0)),
                ('prazo_dias', models.IntegerField(blank=True, null=True)),
                ('obrigatorio', models.BooleanField(default=True)),
                ('config', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='colunas',
                    to='core.planilhafuncionarioconfig',
                )),
            ],
            options={
                'verbose_name': 'Coluna da Planilha',
                'ordering': ['ordem', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='PlanilhaPeriodo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('ano', models.IntegerField()),
                ('mes', models.IntegerField()),
                ('config', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='periodos',
                    to='core.planilhafuncionarioconfig',
                )),
            ],
            options={
                'verbose_name': 'Período da Planilha',
                'ordering': ['-ano', '-mes'],
                'unique_together': {('config', 'ano', 'mes')},
            },
        ),
        migrations.CreateModel(
            name='PlanilhaLinha',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=200)),
                ('ordem', models.IntegerField(default=0)),
                ('periodo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='linhas',
                    to='core.planilhaperiodo',
                )),
            ],
            options={
                'verbose_name': 'Linha da Planilha',
                'ordering': ['ordem', 'label'],
            },
        ),
        migrations.CreateModel(
            name='PlanilhaCelula',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('valor', models.TextField(blank=True, null=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('coluna', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='core.planilhaconfigcoluna',
                )),
                ('linha', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='celulas',
                    to='core.planilhalinha',
                )),
                ('atualizado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='celulas_atualizadas',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Célula da Planilha',
                'unique_together': {('linha', 'coluna')},
            },
        ),
    ]
