from celery import Celery

app = Celery(
    "rei",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)
app.conf.task_default_queue = "rei"