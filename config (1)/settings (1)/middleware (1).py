import logging
from django.utils.deprecation import MiddlewareMixin
from realtorx.custom_auth.models import Logs

logger_4 = logging.getLogger("400_logs")
logger_5 = logging.getLogger("500_logs")


class Log400Response(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_response(self, request, response):
        try:
            if str(response.status_code).startswith("40"):
                if request.user.is_authenticated:
                    logger_4.debug(request.user)
                logger_4.debug(request.get_full_path())
                logger_4.debug(str(response.content))
                logger_4.debug("=" * 50)
                obj_dict = {
                    "server": request.META["HTTP_HOST"],
                    "user": (
                        request.user.full_name if request.user.id is not None else ""
                    ),
                    "path": request.get_full_path() or "",
                    "status": response.status_code or "",
                    "request_content": request.body or "",
                    "response_content": response.content or "",
                }
                log_obj = Logs(**obj_dict)
                log_obj.save()
        except Exception as e:
            logger_4.debug(e.args)
            logger_4.debug("=" * 50)
            pass
        if str(response.status_code) == "403":  # rate limit forbidden 403 to 503
            response.status_code = 503
        return response


class Log500Response(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_response(self, request, response):
        try:
            if str(response.status_code).startswith("50"):
                if request.user.is_authenticated:
                    logger_5.debug(request.user)
                logger_5.debug(request.get_full_path())
                logger_5.debug(str(response.content))
                logger_5.debug("=" * 50)
                obj_dict = {
                    "server": request.META["HTTP_HOST"],
                    "user": (
                        request.user.full_name if request.user.id is not None else ""
                    ),
                    "path": request.get_full_path() or "",
                    "status": response.status_code or "",
                    "request_content": request.body or "",
                    "response_content": response.content or "",
                }
                log_obj = Logs(**obj_dict)
                log_obj.save()
        except Exception as e:
            logger_5.debug(e.args)
            logger_5.debug("=" * 50)
            pass
        return response
