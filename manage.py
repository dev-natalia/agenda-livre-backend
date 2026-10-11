#!/usr/bin/env python
"""Utilitário de linha de comando do Django."""

import os
import sys


def main():
    from config.env import load_dotenv

    load_dotenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
