import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_messagetemplate_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campanha',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=255, verbose_name='Nome da campanha')),
                ('criada_em', models.DateTimeField(default=django.utils.timezone.now)),
                ('total_enviados', models.IntegerField(default=0)),
                ('total_erros', models.IntegerField(default=0)),
                ('total_sem_numero', models.IntegerField(default=0)),
            ],
            options={'verbose_name': 'Campanha', 'verbose_name_plural': 'Campanhas', 'ordering': ['-criada_em']},
        ),
        migrations.CreateModel(
            name='MensagemEnviada',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('condominio', models.CharField(blank=True, max_length=512)),
                ('unidade', models.CharField(blank=True, max_length=255)),
                ('nome', models.CharField(blank=True, max_length=512)),
                ('telefone', models.CharField(max_length=30)),
                ('mensagem', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[('enviado', 'Enviado'), ('respondido', 'Respondido'), ('erro', 'Erro')],
                    default='enviado', max_length=20,
                )),
                ('enviada_em', models.DateTimeField(default=django.utils.timezone.now)),
                ('respondida_em', models.DateTimeField(blank=True, null=True)),
                ('resposta', models.TextField(blank=True)),
                ('campanha', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mensagens',
                    to='core.campanha',
                )),
            ],
            options={'verbose_name': 'Mensagem enviada', 'verbose_name_plural': 'Mensagens enviadas', 'ordering': ['-enviada_em']},
        ),
        migrations.AddIndex(
            model_name='mensagemEnviada',
            index=models.Index(fields=['telefone'], name='core_mensa_telefon_idx'),
        ),
        migrations.AddIndex(
            model_name='mensagemEnviada',
            index=models.Index(fields=['campanha', 'status'], name='core_mensa_campanha_idx'),
        ),
    ]