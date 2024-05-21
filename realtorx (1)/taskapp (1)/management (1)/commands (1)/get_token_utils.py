from django.conf import settings
import requests


class GetTokenCommand:
    def get_token(self):
        # getting every time platform token
        url = "https://api.listhub.com/oauth2/token"
        payload = "grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(
            client_id=settings.CLIENT_ID, client_secret=settings.CLIENT_SECRET
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        req = requests.request("POST", url, headers=headers, data=payload).json()
        return req["access_token"]
