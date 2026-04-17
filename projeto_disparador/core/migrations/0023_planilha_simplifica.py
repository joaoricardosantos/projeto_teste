from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_planilha_redesign'),
    ]

    operations = [
        migrations.DeleteModel(name='PlanilhaColunaRegra'),
        migrations.RemoveField(model_name='planilhafuncionarioconfig', name='linha_cabecalho'),
        migrations.RemoveField(model_name='planilhafuncionarioconfig', name='linha_dados_inicio'),
        migrations.RemoveField(model_name='planilhafuncionarioconfig', name='coluna_label_indice'),
    ]
