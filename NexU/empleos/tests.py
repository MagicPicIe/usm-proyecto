"""
Pruebas de NexU. Ejecutar con:  py manage.py test
"""
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from cuentas.models import Notificacion, Postulante, PreferenciasTest

from . import recomendaciones as rec
from .models import OfertaTrabajo, Postulacion, PyME

PREFS = {
    'anio_carrera': '3', 'categorias': ['gastronomia'], 'jornadas': ['diurna'],
    'dias': ['lun', 'vie'], 'pago_minimo': 25000, 'distancia_max': 10,
}
OFERTA = {'categoria': 'gastronomia', 'jornada': 'diurna', 'dias': ['lun', 'mie', 'vie'],
          'pago': 30000, 'experiencia': 'baja'}


class RecomendacionesTest(TestCase):
    def test_haversine_valparaiso_vina(self):
        # Entre los centros de Valparaíso y Viña hay ~6,2 km
        self.assertAlmostEqual(rec.haversine_km(-33.0472, -71.6127, -33.0245, -71.5518), 6.2, delta=0.2)

    def test_dias_parciales(self):
        self.assertAlmostEqual(rec.puntaje_dias(['lun', 'mie', 'vie'], ['lun', 'vie']), 2 / 3)

    def test_pago_parcial_cerca_del_minimo(self):
        self.assertEqual(rec.puntaje_pago(30000, 25000), 1)
        self.assertAlmostEqual(rec.puntaje_pago(22500, 25000), 0.5)
        self.assertEqual(rec.puntaje_pago(15000, 25000), 0)

    def test_experiencia_segun_anio(self):
        self.assertEqual(rec.experiencias_permitidas('1'), {'sin'})
        self.assertEqual(rec.experiencias_permitidas('4'), {'sin', 'baja'})
        self.assertIn('alta', rec.experiencias_permitidas('egresado'))

    def test_cercania_lineal(self):
        self.assertEqual(rec.puntaje_cercania(0, 10), 100)
        self.assertEqual(rec.puntaje_cercania(5, 10), 50)
        self.assertEqual(rec.puntaje_cercania(15, 10), 0)

    def test_puntaje_total_del_ejemplo(self):
        # preferencias 95, cercanía 80 -> 0.7*95 + 0.3*80 = 90.5 -> 91
        self.assertEqual(rec.calcular_puntaje(OFERTA, PREFS, 2), 91)
        self.assertTrue(rec.es_recomendada(91))


class FlujoTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='ana@usm.cl', email='ana@usm.cl', password='clave-segura-123')
        self.postulante = Postulante.objects.create(
            usuario=self.user, nombres='Ana', apellidos='Rojas', rut='11.111.111-1',
            telefono='+56 9 1111 1111', comuna='valparaiso')
        pyme = PyME.objects.create(nombre='Café', rut='76.123.451-K', rubro='Gastronomía',
                                   comuna='valparaiso', direccion='Cerro Alegre',
                                   telefono='1', correo='a@b.cl')
        self.oferta = OfertaTrabajo.objects.create(
            pyme=pyme, titulo='Lavaplatos', descripcion='x', categoria='gastronomia', pago=30000,
            jornada='diurna', experiencia_requerida='sin', horario='9 a 14', dias=['lun'],
            comuna='valparaiso', latitud=-33.045, longitud=-71.613)

    def test_login_con_correo(self):
        r = self.client.post(reverse('cuentas:login'),
                             {'correo': 'ana@usm.cl', 'contrasena': 'clave-segura-123'})
        self.assertRedirects(r, reverse('empleos:mapa'), fetch_redirect_response=False)

    def test_api_filtra_por_radio(self):
        r = self.client.get(reverse('empleos:api_ofertas'), {'lat': -33.0472, 'lng': -71.6127, 'radio': 1})
        self.assertEqual(r.json()['total'], 1)
        r = self.client.get(reverse('empleos:api_ofertas'), {'lat': -32.93, 'lng': -71.519, 'radio': 1})
        self.assertEqual(r.json()['total'], 0)

    def test_postular_sin_duplicados_y_notifica(self):
        self.client.force_login(self.user)
        url = reverse('empleos:postular', args=[self.oferta.pk])
        r1 = self.client.post(url).json()
        r2 = self.client.post(url).json()
        self.assertEqual(r1['mensaje'], 'Postulaste a Lavaplatos')
        self.assertEqual(r2['mensaje'], 'Ya postulaste a esta oferta')
        self.assertEqual(Postulacion.objects.count(), 1)
        self.assertEqual(Notificacion.objects.filter(usuario=self.user).count(), 1)

    def test_cambio_de_estado_crea_notificacion(self):
        p = Postulacion.objects.create(postulante=self.postulante, oferta=self.oferta)
        p.estado = 'aceptada'
        p.save()
        self.assertEqual(Notificacion.objects.filter(usuario=self.user).count(), 2)

    def test_test_sin_cuenta_se_traspasa_al_iniciar_sesion(self):
        self.client.post(reverse('cuentas:test'), {
            'anio_carrera': '2', 'categorias': ['gastronomia'], 'jornadas': ['diurna'],
            'dias': ['lun'], 'distancia_max': 5, 'pago_minimo': 0})
        self.client.post(reverse('cuentas:login'),
                         {'correo': 'ana@usm.cl', 'contrasena': 'clave-segura-123'})
        self.assertTrue(PreferenciasTest.objects.filter(postulante=self.postulante).exists())


class CargarDatosTest(TestCase):
    def test_no_duplica_y_crea_usuario_de_prueba(self):
        call_command('cargar_datos', stdout=StringIO())
        call_command('cargar_datos', stdout=StringIO())
        self.assertEqual(PyME.objects.count(), 6)
        self.assertEqual(OfertaTrabajo.objects.count(), 32)
        usuario = get_user_model().objects.get(username='nexusprueba')
        self.assertFalse(usuario.is_staff)
        self.assertEqual(usuario.postulante.postulaciones.count(), 2)
        self.assertTrue(hasattr(usuario.postulante, 'preferencias'))

    def test_login_con_nombre_de_usuario(self):
        call_command('cargar_datos', stdout=StringIO())
        r = self.client.post(reverse('cuentas:login'),
                             {'correo': 'nexusprueba', 'contrasena': 'nexus1234'})
        self.assertRedirects(r, reverse('empleos:mapa'), fetch_redirect_response=False)


class LinkedInTest(TestCase):
    def setUp(self):
        self.pyme = PyME.objects.create(nombre='Café', rut='76.123.451-K', rubro='Gastronomía',
                                        comuna='valparaiso', direccion='x', telefono='1', correo='a@b.cl')
        self.oferta = OfertaTrabajo.objects.create(
            pyme=self.pyme, titulo='Garzón', descripcion='x', categoria='gastronomia', pago=30000,
            jornada='diurna', experiencia_requerida='sin', horario='9 a 14', dias=['lun'],
            comuna='valparaiso', latitud=-33.045, longitud=-71.613)

    def test_formatos_de_enlace(self):
        from .linkedin import id_empleo, normalizar_url_empleo, slug_empresa
        self.assertEqual(id_empleo('https://cl.linkedin.com/jobs/view/garzon-3912345678?trk=x'), '3912345678')
        self.assertEqual(id_empleo('https://www.linkedin.com/jobs/search/?currentJobId=3912345678'), '3912345678')
        self.assertIsNone(id_empleo('https://linkedin.com.falso.cl/jobs/view/3912345678'))
        self.assertEqual(normalizar_url_empleo('https://cl.linkedin.com/jobs/view/garzon-3912345678'),
                         'https://www.linkedin.com/jobs/view/3912345678/')
        self.assertEqual(slug_empresa('https://www.linkedin.com/company/cafe-puerto/about/'), 'cafe-puerto')

    def test_no_se_verifica_sin_enlace(self):
        self.oferta.verificada = True
        self.oferta.save()
        self.oferta.refresh_from_db()
        self.assertFalse(self.oferta.verificada)

    def test_cambiar_enlace_quita_la_verificacion(self):
        self.oferta.linkedin_url = 'https://www.linkedin.com/jobs/view/1111111111/'
        self.oferta.verificada = True
        self.oferta.save()
        self.assertIsNotNone(self.oferta.fecha_verificacion)
        self.oferta.linkedin_url = 'https://www.linkedin.com/jobs/view/2222222222/'
        self.oferta.save()
        self.oferta.refresh_from_db()
        self.assertFalse(self.oferta.verificada)

    def test_api_filtra_verificadas(self):
        url = reverse('empleos:api_ofertas')
        params = {'lat': -33.0472, 'lng': -71.6127, 'radio': 5, 'verificadas': 1}
        self.assertEqual(self.client.get(url, params).json()['total'], 0)
        self.oferta.linkedin_url = 'https://www.linkedin.com/jobs/view/1111111111/'
        self.oferta.verificada = True
        self.oferta.save()
        datos = self.client.get(url, params).json()
        self.assertEqual(datos['total'], 1)
        self.assertTrue(datos['ofertas'][0]['verificada'])
