from django.contrib.auth.models import UserManager


class ApplicationUserManager(UserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        if not email:
            # using None instead of empty string if there's no email to bypass unique=True constraint
            return None
        return super().normalize_email(email)

    def get_by_natural_key(self, value):
        return self.get(
            **{
                "{user_name_field}__iexact".format(
                    user_name_field=self.model.USERNAME_FIELD
                ): value
            }
        )
