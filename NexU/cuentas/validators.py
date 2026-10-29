"""Validación del RUT chileno (formato y dígito verificador)."""
import re

from django.core.exceptions import ValidationError


def limpiar_rut(rut):
    """Quita puntos, guion y espacios; deja la K en mayúscula: '12.345.678-k' -> '12345678K'."""
    return re.sub(r'[^0-9kK]', '', str(rut or '')).upper()


def calcular_dv(numero):
    """
    Calcula el dígito verificador con el algoritmo módulo 11:
    se multiplican los dígitos de derecha a izquierda por 2, 3, 4, 5, 6, 7
    (y se repite), se suman, y el DV es 11 - (suma % 11).
    11 se escribe 0 y 10 se escribe K.
    """
    suma = 0
    multiplicador = 2
    for digito in reversed(str(numero)):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return '0'
    if resto == 10:
        return 'K'
    return str(resto)


def formatear_rut(rut):
    """'123456785' -> '12.345.678-5'."""
    limpio = limpiar_rut(rut)
    cuerpo, dv = limpio[:-1], limpio[-1]
    cuerpo = f'{int(cuerpo):,}'.replace(',', '.')
    return f'{cuerpo}-{dv}'


def validar_rut(valor):
    limpio = limpiar_rut(valor)
    if not re.fullmatch(r'\d{7,8}[0-9K]', limpio):
        raise ValidationError('El RUT debe tener el formato 12.345.678-9.')
    if calcular_dv(limpio[:-1]) != limpio[-1]:
        raise ValidationError('El dígito verificador del RUT no es válido.')
