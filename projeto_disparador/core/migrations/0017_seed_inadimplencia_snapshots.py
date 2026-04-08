from django.db import migrations


SNAPSHOTS = [
    (2024, 12, "13196218.70"),
    (2025,  3, "13417763.63"),
    (2025,  6, "13670894.26"),
    (2025, 12, "14262702.40"),
    (2026,  1, "14377916.15"),
    (2026,  2, "14461046.82"),
    (2026,  3, "14697071.67"),
    (2026,  4, "14701684.83"),
]


def seed_snapshots(apps, schema_editor):
    InadimplenciaSnapshot = apps.get_model("core", "InadimplenciaSnapshot")
    for ano, mes, total in SNAPSHOTS:
        InadimplenciaSnapshot.objects.update_or_create(
            ano=ano, mes=mes, defaults={"total": total}
        )


def unseed_snapshots(apps, schema_editor):
    InadimplenciaSnapshot = apps.get_model("core", "InadimplenciaSnapshot")
    for ano, mes, _ in SNAPSHOTS:
        InadimplenciaSnapshot.objects.filter(ano=ano, mes=mes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_add_condominio_id_valido"),
    ]

    operations = [
        migrations.RunPython(seed_snapshots, reverse_code=unseed_snapshots),
    ]
