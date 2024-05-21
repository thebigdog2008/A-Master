from django import template
from django.template.defaultfilters import stringfilter
import contextlib

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def phonenumber(value: str):
    """Checks whether the value is an US, Australian or other number
    and returns the formatted version of the value.

    US => (xxx) xxx-xxxx
    Australia => (+61) xxx xxx xxx
    Other => value
    """
    formatted_number = (
        value  # the default value of formatted number is the value itself
    )

    with contextlib.suppress(Exception):  # suppress any exception
        if value.startswith("+1"):
            number = value.split("+1")[-1]
            formatted_number = (
                f"({number[:3]}) {number[3:6]}-{number[6:10]}"  # (xxx) xxx-xxxx
            )
        elif value.startswith("+61"):
            number = value
            formatted_number = f"({number[:3]}) {number[3:6]} {number[6:9]} {number[9:12]}"  # (+61) xxx xxx xxx

    return formatted_number
