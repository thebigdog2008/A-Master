class AuthBackendWithExtraData:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_extra_data = {}

    def get_user_details(self, response):
        details = super().get_user_details(response)
        details.update(self.user_extra_data)
        return details

    def do_auth(self, access_token, *args, **kwargs):
        if "user_extra_data" in kwargs:
            self.user_extra_data = kwargs["user_extra_data"]

        return super().do_auth(access_token, *args, **kwargs)
