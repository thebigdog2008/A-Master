from templated_email.backends.vanilla_django import TemplateBackend

from realtorx.mailing.tasks import send_email


class AsyncTemplateBackend(TemplateBackend):
    def send_async(self, *args, **kwargs):
        send_email.delay(
            {
                "template_prefix": self.template_prefix,
                "template_suffix": self.template_suffix,
            },
            *args,
            **kwargs
        )

    def send_sync(self, *args, **kwargs):
        return super(AsyncTemplateBackend, self).send(*args, **kwargs)

    def send(self, *args, **kwargs):
        return self.send_async(*args, **kwargs)
