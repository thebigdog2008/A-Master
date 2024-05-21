import requests

from realtorx.taskapp import app


@app.task(ignore_result=True, time_limit=60)
def send_pong_to_uptimebot(pong_to):
    requests.get(pong_to)
