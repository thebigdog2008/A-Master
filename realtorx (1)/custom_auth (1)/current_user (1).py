from threading import local

_user = local()


class CurrentUserMiddleware(object):
    def process_request(self, request):
        _user.value = request.user

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _user.value = request.user
        return self.get_response(request)

    def process_exception(self, request, exception):
        _user.value = request.user


def get_current_user():
    return _user.value
