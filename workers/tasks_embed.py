from workers.celery_app import app


@app.task
def reembed_all() -> str:
    return "not implemented in demo"