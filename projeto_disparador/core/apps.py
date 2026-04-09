import threading
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Inicia o scheduler de snapshot diário em background
        _iniciar_scheduler_snapshot()


def _iniciar_scheduler_snapshot():
    """
    Roda em thread daemon. Verifica uma vez por hora se já existe
    snapshot do mês/dia atual — se não existir (ou se for um novo dia),
    dispara a captura via Superlógica e persiste no banco.
    """
    import time
    from datetime import datetime, date

    def _loop():
        ultimo_dia_capturado = None

        # Aguarda 30s para o Django terminar de inicializar
        time.sleep(30)

        while True:
            try:
                hoje = date.today()
                if hoje != ultimo_dia_capturado:
                    _capturar_agora(hoje)
                    ultimo_dia_capturado = hoje
            except Exception:
                pass
            # Verifica novamente em 1 hora
            time.sleep(3600)

    t = threading.Thread(target=_loop, daemon=True, name="snapshot-scheduler")
    t.start()


def _capturar_agora(hoje):
    from core.admin_api import _calcular_dashboard
    from core.models import InadimplenciaSnapshot
    from datetime import datetime

    resultado = _calcular_dashboard(forcar=True)
    total = float(resultado.get("total_inadimplencia", 0))
    if total > 0:
        InadimplenciaSnapshot.objects.update_or_create(
            ano=hoje.year,
            mes=hoje.month,
            defaults={"total": total},
        )
