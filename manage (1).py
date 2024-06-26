#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    DJANGO_SETTINGS_MODULE = os.environ.get(
        "DJANGO_SETTINGS_MODULE", "config.settings.prod"
    )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS_MODULE)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
