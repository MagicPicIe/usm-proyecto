from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from .validators import calcular_dv, formatear_rut, validar_rut


class RutTest(SimpleTestCase):
    def test_digito_verificador(self):
        self.assertEqual(calcular_dv('11111111'), '1')
        self.assertEqual(calcular_dv('76123451'), 'K')

    def test_formatos_validos(self):
        for rut in ('11.111.111-1', '111111111', '76123451-k'):
            validar_rut(rut)

    def test_rut_invalido(self):
        with self.assertRaises(ValidationError):
            validar_rut('11.111.111-2')
        with self.assertRaises(ValidationError):
            validar_rut('abc')

    def test_formatear(self):
        self.assertEqual(formatear_rut('123456785'), '12.345.678-5')


class CsrfTest(TestCase):
    def test_token_viejo_recarga_con_aviso_en_vez_de_403(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.get(reverse('cuentas:login'))
        r = cliente.post(reverse('cuentas:login'),
                         {'correo': 'a@b.cl', 'contrasena': 'x', 'csrfmiddlewaretoken': 'viejo' * 8},
                         HTTP_REFERER='http://testserver/cuentas/login/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], 'http://testserver/cuentas/login/')
