#!/usr/bin/env python
"""Utilidad de línea de comandos de Django para el proyecto NexU."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexu.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Instalaste las dependencias con "
            "'py -m pip install -r requirements.txt'?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
