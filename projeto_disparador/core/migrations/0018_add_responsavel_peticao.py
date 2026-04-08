from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_seed_inadimplencia_snapshots'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResponsavelPeticao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255)),
                ('funcao', models.CharField(blank=True, default='', max_length=255)),
                ('padrao', models.BooleanField(default=False)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Responsável pela Petição',
                'ordering': ['-padrao', 'nome'],
            },
        ),
    ]
