from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.template.response import TemplateResponse
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from .resources import ApplicationUserResource
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime, timedelta


@never_cache
def account_confirm(
    request,
    uidb64=None,
    token=None,
    template_name="custom_auth/account_confirm.html",
    token_generator=default_token_generator,
    current_app=None,
    extra_context=None,
):
    UserModel = get_user_model()  # noqa S101
    if uidb64 is None or token is None:
        raise RuntimeError("uidb64 or token should be provided")

    try:
        # urlsafe_base64_decode() decodes to bytestring on Python 3
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None

    if user is not None and token_generator.check_token(user, token):
        validlink = True
        title = _("Account confirmed successfully")
    else:
        validlink = False
        title = _("Account confirmed unsuccessfully")

    context = {
        "title": title,
        "validlink": validlink,
    }

    if extra_context is not None:
        context.update(extra_context)

    if current_app is not None:
        request.current_app = current_app

    return TemplateResponse(request, template_name, context)


@user_passes_test(lambda u: u.is_superuser)
def userReportAdmin(request):
    if request.method == "GET":
        return render(request, "user_report.html")

    if request.method == "POST":
        from_date = request.POST["from_date"]
        to_date = request.POST["to_date"]

        from_date = datetime.strptime(from_date, "%Y-%m-%d")
        to_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)

        queryset = ApplicationUser.objects.filter(
            last_login__range=(from_date, to_date)
        ).exclude(is_superuser=True)

        user_resource = ApplicationUserResource()
        dataset = user_resource.export(queryset)
        response = HttpResponse(dataset.csv, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="user.csv"'
        return response
