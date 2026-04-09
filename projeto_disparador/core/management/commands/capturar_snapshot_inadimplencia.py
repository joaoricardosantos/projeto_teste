"""
Management command: capturar_snapshot_inadimplencia

Busca o total de inadimplência atual via Superlógica e salva/atualiza
o snapshot do mês corrente no banco de dados.

Uso:
    python manage.py capturar_snapshot_inadimplencia

Deve ser agendado via cron para rodar uma vez por dia (ex: 06:00).
"""
from django.core.management.base import BaseCommand
from datetime import datetime


class Command(BaseCommand):
    help = "Captura snapshot diário de inadimplência e persiste no banco"

    def handle(self, *args, **options):
        from core.admin_api import _calcular_dashboard
        from core.models import InadimplenciaSnapshot

        agora = datetime.now()
        self.stdout.write(f"[{agora:%d/%m/%Y %H:%M}] Iniciando captura de snapshot...")

        try:
            resultado = _calcular_dashboard(forcar=True)
            total = float(resultado.get("total_inadimplencia", 0))

            obj, created = InadimplenciaSnapshot.objects.update_or_create(
                ano=agora.year,
                mes=agora.month,
                defaults={"total": total},
            )

            acao = "criado" if created else "atualizado"
            self.stdout.write(
                self.style.SUCCESS(
                    f"Snapshot {obj.mes:02d}/{obj.ano} {acao}: R$ {total:,.2f}"
                )
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro ao capturar snapshot: {e}"))
            raise
