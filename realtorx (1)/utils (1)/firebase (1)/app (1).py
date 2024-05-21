import base64

from django.conf import settings

from firebase_admin import App, db, initialize_app
from firebase_admin.credentials import Certificate


class Firebase:
    @classmethod
    def get_credentials(cls):
        return Certificate(
            {
                "type": "service_account",
                "project_id": settings.FIREBASE_PROJECT_ID,
                "private_key": base64.decodebytes(
                    settings.FIREBASE_SERVICE_ACCOUNT_PRIVATE_KEY.encode()
                ).decode(),
                "client_email": settings.FIREBASE_SERVICE_ACCOUNT_CLIENT_EMAIL,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )

    @classmethod
    def get_app(cls) -> App:
        if not hasattr(cls, "_firebase_app"):
            cls._firebase_app = initialize_app(
                credential=cls.get_credentials(),
                options={"databaseURL": "https://" + settings.FIREBASE_DATABASE},
            )

        return cls._firebase_app

    @classmethod
    def get_data(cls, path: str) -> any:
        app = cls.get_app()
        return db.reference(path=cls.get_path(path), app=app).get()

    @classmethod
    def get_names(cls, path: str) -> list:
        app = cls.get_app()
        data = db.reference(path=cls.get_path(path), app=app).get(shallow=False)
        if not data:
            return []

        return list(data.keys())

    @classmethod
    def set(cls, path: str, value: any) -> None:
        app = cls.get_app()
        db.reference(path=cls.get_path(path), app=app).set(value)

    @classmethod
    def get_path(cls, path):
        return "/" + settings.FIREBASE_BRANCH + path
