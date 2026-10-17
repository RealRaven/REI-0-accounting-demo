from app.services.matching_service import match_invoice
from workers.celery_app import app


@app.task
def reconcile() -> str:
    # demo: no persistent fetch here; see scripts/demo_run.py for the wired path
    return "reconcile stub"