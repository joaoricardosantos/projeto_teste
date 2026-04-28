from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_planilha_simplifica'),
    ]

    operations = [
        migrations.CreateModel(
            name='CondominioDriveMap',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False)),
                ('condominio_id', models.IntegerField(unique=True)),
                ('condominio_nome', models.CharField(blank=True, max_length=255)),
                ('drive_folder_id', models.CharField(max_length=200)),
                ('drive_folder_nome', models.CharField(blank=True, max_length=255)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Mapeamento Condomínio → Drive',
                'ordering': ['condominio_nome'],
            },
        ),
    ]
