from templated_email import get_connection

from realtorx.taskapp import app


@app.task(ignore_result=True)
def send_email(connection_kwargs, *args, **kwargs):
    backend = get_connection(**connection_kwargs)
    backend.send_sync(*args, **kwargs)
