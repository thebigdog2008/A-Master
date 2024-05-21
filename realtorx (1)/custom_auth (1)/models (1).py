import uuid
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from localflavor.us.models import USStateField
from rest_framework_simplejwt.tokens import RefreshToken
from realtorx.custom_auth.managers import ApplicationUserManager
from templated_email import send_templated_mail
from realtorx.houses.models.agent import Agent


class BaseProfile(models.Model):
    full_name = models.CharField(_("Full Name"), max_length=300)
    email = models.EmailField(_("email address"), unique=True, null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def avatar_thumbnail_square_url(self):
        return self.avatar_thumbnail_square.hash_id if self.avatar_thumbnail_square else None


class ApplicationUser(models.Model):
    uuid = models.UUIDField(
        verbose_name=_("uuid"), unique=True, default=uuid.uuid4, editable=False
    )
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        validators=[
            validators.RegexValidator(
                r"^[\w.@+-]+$",
                _(
                    "Enter a valid username. This value may contain only letters, numbers, and @/./+/-/_ characters."
                ),
            ),
        ],
    )
    full_name = models.CharField(_("Full Name"), max_length=300)
    email = models.EmailField(_("email address"), unique=True, null=True, blank=True)
    state = USStateField(_("State"))
    agent_id = models.ForeignKey(
        Agent,
        null=True,
        blank=True,
        related_name="agents",
        on_delete=models.DO_NOTHING,
    )
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    send_email_with_jwt_token = models.BooleanField(default=True)
    jwt_token = models.CharField(max_length=255, null=True, blank=True)
    email_notifications_enabled = models.BooleanField(
        verbose_name=_("Enable email notification"), default=True
    )

    verified_user = models.BooleanField(_("Verified user"), default=True)
    objects = ApplicationUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("id",)

    def __str__(self):
        return self.full_name

    def email_user(self, template_name, extra_context=None, **kwargs):
        if not self.email:
            return

        context = {
            "user": self,
            "site": site.objects.get_current(),
            "email_type": template_name,
        }
        context.update(extra_context or {})
        send_templated_mail(
            self,
            template_name,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            context,
            **kwags
        )


class PasswordResetId(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Password reset id")


class EmailVerificationId(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    expiration_time = models.DateTimeField()

    class Meta:
        verbose_name = _("Email verification id")

    def generate_jwt_token(self):
        refresh = RefreshToken.for_user(self.user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class Logs(models.Model):
    server = models.CharField(max_length=100, null=True, blank=True)
    user = models.CharField(max_length=100, null=True, blank=True)
    path = models.CharField(max_length=1000, null=True, blank=True)
    status = models.CharField(max_length=3, null=True, blank=True)
    request_content = models.TextField()
    response_content = models.TextField()
    date = models.DateTimeField(auto_now_add=True)


class EmailsRestriction(models.Model):
    send_emails_on = models.BooleanField(default=False)
    recipient_list = ArrayField(
        models.CharField(max_length=100, null=True, blank=True),
        default=list,
        null=True,
        blank=True,

    )
    receipt_data = models.CharField(max_length=32, unique=True, db_index=True)
