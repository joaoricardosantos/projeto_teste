import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_planilha_funcionario'),
    ]

    operations = [
        # Drop tabelas que não serão mais usadas (dados via Google Sheets)
        migrations.DeleteModel(name='PlanilhaCelula'),
        migrations.DeleteModel(name='PlanilhaLinha'),
        migrations.DeleteModel(name='PlanilhaPeriodo'),
        migrations.DeleteModel(name='PlanilhaConfigColuna'),

        # Adiciona campos de integração ao config
        migrations.AddField(
            model_name='planilhafuncionarioconfig',
            name='spreadsheet_id',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='planilhafuncionarioconfig',
            name='linha_cabecalho',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='planilhafuncionarioconfig',
            name='linha_dados_inicio',
            field=models.IntegerField(default=2),
        ),
        migrations.AddField(
            model_name='planilhafuncionarioconfig',
            name='coluna_label_indice',
            field=models.IntegerField(default=0),
        ),

        # Cria nova tabela de regras de cor por coluna
        migrations.CreateModel(
            name='PlanilhaColunaRegra',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('coluna_nome', models.CharField(max_length=200)),
                ('tipo', models.CharField(
                    choices=[('data', 'Data'), ('booleano', 'Booleano'), ('texto', 'Texto')],
                    default='texto',
                    max_length=20,
                )),
                ('prazo_dias', models.IntegerField(blank=True, null=True)),
                ('config', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='regras',
                    to='core.planilhafuncionarioconfig',
                )),
            ],
            options={
                'verbose_name': 'Regra de Coluna da Planilha',
                'ordering': ['coluna_nome'],
            },
        ),
    ]
