"""
python manage.py cargar_datos

Crea 6 PyMEs, 32 ofertas activas con coordenadas reales del Gran Valparaíso
y un usuario de prueba normal (no administrador):

    usuario:    nexusprueba   (o el correo nexusprueba@nexu.cl)
    contraseña: nexus1234

Se puede ejecutar varias veces: usa update_or_create / get_or_create, así que
no duplica nada. Cada vez deja la contraseña del usuario de prueba en nexus1234.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from cuentas.models import Postulante, PreferenciasTest
from cuentas.validators import calcular_dv, formatear_rut
from empleos.models import OfertaTrabajo, Postulacion, PyME


def rut(numero):
    """Arma un RUT válido calculando su dígito verificador."""
    return formatear_rut(f'{numero}{calcular_dv(numero)}')


PYMES = [
    {'clave': 'cafe', 'nombre': 'Café Puerto Alegre', 'rut': rut(76123451), 'rubro': 'Gastronomía',
     'comuna': 'valparaiso', 'direccion': 'Almirante Montt 254, Cerro Alegre',
     'telefono': '+56 32 245 1180', 'correo': 'contacto@cafepuertoalegre.cl'},
    {'clave': 'minimarket', 'nombre': 'Minimarket Las Palmas', 'rut': rut(77234562), 'rubro': 'Comercio',
     'comuna': 'vina', 'direccion': 'Av. Libertad 1020, Viña del Mar',
     'telefono': '+56 32 268 4410', 'correo': 'ventas@lpalmas.cl'},
    {'clave': 'logistica', 'nombre': 'Logística Costa Central', 'rut': rut(76345673),
     'rubro': 'Bodega y reparto', 'comuna': 'quilpue', 'direccion': 'Av. Los Carrera 1450, Quilpué',
     'telefono': '+56 32 291 7730', 'correo': 'rrhh@costacentral.cl'},
    {'clave': 'academia', 'nombre': 'Academia Pitágoras', 'rut': rut(77456784), 'rubro': 'Educación',
     'comuna': 'vina', 'direccion': '5 Oriente 260, Viña del Mar',
     'telefono': '+56 9 8812 4455', 'correo': 'hola@academiapitagoras.cl'},
    {'clave': 'bytefix', 'nombre': 'ByteFix Soporte TI', 'rut': rut(76567895), 'rubro': 'Tecnología',
     'comuna': 'valparaiso', 'direccion': 'Av. Brasil 1680, Valparaíso',
     'telefono': '+56 9 7720 3311', 'correo': 'equipo@bytefix.cl'},
    {'clave': 'marea', 'nombre': 'Producciones Marea Eventos', 'rut': rut(77678906), 'rubro': 'Eventos',
     'comuna': 'concon', 'direccion': 'Av. Borgoño 21500, Concón',
     'telefono': '+56 9 6655 1020', 'correo': 'staff@mareaeventos.cl'},
]

L, M, X, J, V, S, D = 'lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom'

# (pyme, título, categoría, pago, jornada, experiencia, horario, días, comuna, lat, lng, descripción)
OFERTAS = [
    # --- Gastronomía ---
    ('cafe', 'Lavaplatos', 'gastronomia', 25000, 'nocturna', 'sin', '19:00 a 01:00', [V, S],
     'valparaiso', -33.0429, -71.6268,
     'Apoyo en cocina lavando loza, ollas y utensilios durante el servicio de la noche. '
     'Se entrega colación y uniforme. Ideal como primer trabajo.'),
    ('cafe', 'Garzón/a fin de semana', 'gastronomia', 30000, 'diurna', 'baja', '11:00 a 18:00', [S, D],
     'valparaiso', -33.0418, -71.6255,
     'Atención de mesas en terraza con vista a la bahía. Propinas aparte. '
     'Se valora experiencia previa atendiendo público.'),
    ('cafe', 'Ayudante de cocina', 'gastronomia', 28000, 'diurna', 'baja', '08:00 a 15:00', [L, M, X],
     'valparaiso', -33.0389, -71.6280,
     'Preparación de ingredientes, montaje de platos fríos y orden de la cocina en local '
     'cercano a Plaza Sotomayor.'),
    ('cafe', 'Barista part-time', 'gastronomia', 22000, 'part_time', 'sin', '16:00 a 20:00',
     [L, X, V], 'vina', -33.0180, -71.5490,
     'Preparación de café de especialidad y atención en caja. Te capacitamos en '
     'extracción y leche texturizada.'),
    ('cafe', 'Cocinero/a turno noche', 'gastronomia', 45000, 'nocturna', 'alta', '18:00 a 02:00',
     [J, V, S], 'vina', -33.0247, -71.5530,
     'Responsable de la línea caliente en el servicio nocturno. Se requiere experiencia '
     'comprobable en cocina de restaurante.'),
    # --- Comercio y ventas ---
    ('minimarket', 'Cajero/a', 'comercio', 24000, 'diurna', 'sin', '09:00 a 15:00', [L, M, X, J],
     'vina', -33.0140, -71.5500,
     'Atención en caja, cobro con efectivo y tarjeta, y apoyo en reposición liviana.'),
    ('minimarket', 'Reponedor/a nocturno', 'comercio', 27000, 'nocturna', 'sin', '22:00 a 05:00',
     [D, L], 'vina', -33.0170, -71.5580,
     'Reposición de góndolas y control de fechas de vencimiento con el local cerrado.'),
    ('minimarket', 'Vendedor/a tienda de ropa', 'comercio', 20000, 'part_time', 'baja',
     '17:00 a 21:00', [M, J, S], 'vina', -33.0100, -71.5490,
     'Venta y orden de tienda en módulo de Marina Arauco. Buen trato con clientes.'),
    ('minimarket', 'Promotor/a de degustaciones', 'comercio', 30000, 'un_dia', 'sin',
     '10:00 a 18:00', [S], 'concon', -32.9245, -71.5220,
     'Un sábado de degustación de productos locales en supermercado de Concón.'),
    # --- Bodega y logística ---
    ('logistica', 'Bodeguero/a', 'bodega', 32000, 'diurna', 'baja', '08:00 a 17:00', [L, M, X, J, V],
     'quilpue', -33.0500, -71.4450,
     'Recepción y despacho de mercadería, orden de bodega y apoyo en carga con transpaleta.'),
    ('logistica', 'Auxiliar de inventario', 'bodega', 35000, 'un_dia', 'sin', '08:00 a 18:00', [D],
     'villa_alemana', -33.0422, -71.3733,
     'Conteo de inventario anual durante un domingo. Se entrega almuerzo.'),
    ('logistica', 'Operario/a de picking nocturno', 'bodega', 38000, 'nocturna', 'baja',
     '22:00 a 06:00', [L, M, X], 'quilpue', -33.0560, -71.4300,
     'Preparación de pedidos para despacho temprano. Trabajo en equipo y orden.'),
    ('logistica', 'Ayudante de bodega', 'bodega', 26000, 'part_time', 'sin', '14:00 a 19:00',
     [J, V], 'villa_alemana', -33.0440, -71.3800,
     'Etiquetado, embalaje y orden de productos en bodega pequeña.'),
    # --- Reparto ---
    ('logistica', 'Repartidor/a en bicicleta', 'reparto', 18000, 'part_time', 'sin',
     '12:00 a 16:00', [L, X, V], 'vina', -33.0270, -71.5420,
     'Reparto de pedidos livianos en el plan de Viña. Se pide bicicleta propia y casco.'),
    ('logistica', 'Repartidor/a con licencia B', 'reparto', 42000, 'diurna', 'alta',
     '08:00 a 17:00', [M, J, S], 'quilpue', -33.0476, -71.4427,
     'Reparto con furgón de la empresa entre Quilpué, Villa Alemana y Viña. '
     'Licencia clase B y experiencia en reparto.'),
    ('logistica', 'Peoneta para mudanza', 'reparto', 30000, 'un_dia', 'sin', '09:00 a 17:00', [S],
     'valparaiso', -33.0300, -71.6400,
     'Apoyo en carga y descarga para una mudanza en Playa Ancha.'),
    # --- Atención al cliente ---
    ('cafe', 'Recepcionista de hostal', 'atencion', 26000, 'diurna', 'baja', '08:00 a 14:00',
     [S, D], 'valparaiso', -33.0425, -71.6270,
     'Check-in de huéspedes, reservas y recomendaciones turísticas. Inglés básico deseable.'),
    ('marea', 'Anfitrión/a de turismo en cerros', 'atencion', 28000, 'un_dia', 'sin',
     '10:00 a 16:00', [D], 'valparaiso', -33.0365, -71.6305,
     'Recibir grupos de turistas en Barrio Puerto y acompañarlos en un recorrido guiado.'),
    ('bytefix', 'Ejecutivo/a de atención telefónica', 'atencion', 21000, 'part_time', 'baja',
     '15:00 a 19:00', [L, M, X, J, V], 'valparaiso', -33.0450, -71.6200,
     'Atención de llamadas y correos de clientes, registro de casos en sistema.'),
    # --- Tutorías y educación ---
    ('academia', 'Tutor/a de matemáticas', 'tutorias', 20000, 'part_time', 'baja', '17:00 a 20:00',
     [M, J], 'vina', -33.0185, -71.5495,
     'Clases de reforzamiento de álgebra y cálculo para estudiantes de enseñanza media.'),
    ('academia', 'Tutor/a de inglés', 'tutorias', 25000, 'part_time', 'alta', '18:00 a 21:00',
     [L, X], 'vina', -33.0290, -71.5480,
     'Clases de conversación en inglés nivel intermedio. Se requiere nivel avanzado acreditable.'),
    ('academia', 'Apoyo ensayo PAES de física', 'tutorias', 30000, 'un_dia', 'baja',
     '09:00 a 14:00', [S], 'valparaiso', -33.0350, -71.5960,
     'Apoyo en ensayo PAES: resolución de dudas y corrección de ejercicios.'),
    # --- Tecnología ---
    ('bytefix', 'Soporte TI', 'tecnologia', 35000, 'diurna', 'baja', '09:00 a 18:00', [L, M, X, J, V],
     'valparaiso', -33.0455, -71.6190,
     'Soporte a usuarios en oficinas: instalación de software, impresoras y redes básicas.'),
    ('bytefix', 'Formateo y mantención de PCs', 'tecnologia', 50000, 'un_dia', 'alta',
     '09:00 a 19:00', [S], 'concon', -32.9530, -71.5450,
     'Formatear y dejar operativos 15 computadores de un colegio. Se necesita experiencia.'),
    ('bytefix', 'Ayudante de desarrollo web', 'tecnologia', 40000, 'part_time', 'alta',
     '14:00 a 18:00', [M, J], 'vina', -33.0245, -71.5518,
     'Apoyo en sitios web de PyMEs con HTML, CSS y Django. Trabajo híbrido.'),
    ('bytefix', 'Community manager', 'tecnologia', 23000, 'part_time', 'baja', '10:00 a 13:00',
     [L, X, V], 'quilpue', -33.0480, -71.4410,
     'Gestión de redes sociales de comercios locales: publicaciones, fotos y respuestas.'),
    # --- Eventos ---
    ('marea', 'Staff de eventos', 'eventos', 35000, 'nocturna', 'sin', '19:00 a 03:00', [V, S],
     'vina', -33.0255, -71.5525,
     'Control de acceso, orden y apoyo general en eventos nocturnos.'),
    ('marea', 'Montaje de escenario', 'eventos', 40000, 'un_dia', 'baja', '07:00 a 16:00', [V],
     'concon', -32.9300, -71.5190,
     'Armado de escenario, carpas e iluminación para festival al aire libre.'),
    ('marea', 'Guardarropía en matrimonio', 'eventos', 30000, 'nocturna', 'sin', '20:00 a 04:00',
     [S], 'concon', -32.9350, -71.5300,
     'Recepción y orden de abrigos de invitados en centro de eventos.'),
    ('marea', 'Animador/a infantil', 'eventos', 35000, 'un_dia', 'baja', '15:00 a 19:00', [D],
     'quilpue', -33.0520, -71.4380,
     'Animación de cumpleaños infantil con juegos y pintacaritas. Materiales incluidos.'),
    ('marea', 'Garzón/a para coctel', 'eventos', 32000, 'nocturna', 'baja', '19:00 a 00:00', [J],
     'villa_alemana', -33.0410, -71.3700,
     'Servicio de coctel en evento corporativo. Se pide camisa blanca y pantalón negro.'),
    ('minimarket', 'Encargado/a de turno', 'comercio', 38000, 'diurna', 'alta', '08:00 a 16:00',
     [L, M, X, J, V], 'concon', -32.9280, -71.5170,
     'Supervisión de cajas y reponedores, cuadratura de caja y atención de proveedores.'),
]


# --- Usuario de prueba (postulante normal, sin permisos de administrador) ---
USUARIO_PRUEBA = {
    'username': 'nexusprueba',
    'email': 'nexusprueba@nexu.cl',
    'password': 'nexus1234',
}
POSTULANTE_PRUEBA = {
    'nombres': 'Nexus', 'apellidos': 'Prueba', 'rut': rut(15555555),
    'telefono': '+56 9 5555 5555', 'comuna': 'vina',
}
# Test ya respondido, para ver recomendaciones apenas entra
TEST_PRUEBA = {
    'carrera': 'informatica',
    'anio_carrera': '3',
    'categorias': ['gastronomia', 'comercio', 'tecnologia', 'eventos'],
    'jornadas': ['diurna', 'part_time', 'un_dia'],
    'dias': ['lun', 'mar', 'mie', 'jue', 'vie', 'sab'],
    'distancia_max': 10,
    'pago_minimo': 15000,
}
}
# Postulaciones de ejemplo: (título de la oferta, estado)
POSTULACIONES_PRUEBA = [
    ('Barista part-time', 'pendiente'),
    ('Staff de eventos', 'aceptada'),
]


class Command(BaseCommand):
    help = 'Carga PyMEs y ofertas de prueba (no duplica si se ejecuta varias veces).'

    @transaction.atomic
    def handle(self, *args, **options):
        pymes = {}
        for datos in PYMES:
            datos = dict(datos)
            clave = datos.pop('clave')
            pyme, creada = PyME.objects.update_or_create(rut=datos['rut'], defaults=datos)
            pymes[clave] = pyme
            self.stdout.write(f"{'Creada' if creada else 'Actualizada'} PyME: {pyme.nombre}")

        nuevas = 0
        for (clave, titulo, categoria, pago, jornada, experiencia, horario, dias,
             comuna, lat, lng, descripcion) in OFERTAS:
            _, creada = OfertaTrabajo.objects.update_or_create(
                pyme=pymes[clave], titulo=titulo,
                defaults={
                    'descripcion': descripcion, 'categoria': categoria, 'pago': pago,
                    'jornada': jornada, 'experiencia_requerida': experiencia,
                    'horario': horario, 'dias': dias, 'comuna': comuna,
                    'latitud': lat, 'longitud': lng, 'activa': True,
                })
            nuevas += int(creada)

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {len(PYMES)} PyMEs y {len(OFERTAS)} ofertas '
            f'({nuevas} nuevas, {len(OFERTAS) - nuevas} actualizadas).'))

        self.crear_usuario_prueba(pymes)

    def crear_usuario_prueba(self, pymes):
        User = get_user_model()
        usuario, creado = User.objects.get_or_create(
            username=USUARIO_PRUEBA['username'],
            defaults={'email': USUARIO_PRUEBA['email'],
                      'first_name': POSTULANTE_PRUEBA['nombres'],
                      'last_name': POSTULANTE_PRUEBA['apellidos']})
        # Siempre usuario normal, activo y con la contraseña conocida
        usuario.email = USUARIO_PRUEBA['email']
        usuario.is_staff = False
        usuario.is_superuser = False
        usuario.is_active = True
        usuario.set_password(USUARIO_PRUEBA['password'])
        usuario.save()

        postulante, _ = Postulante.objects.update_or_create(
            usuario=usuario, defaults=POSTULANTE_PRUEBA)
        PreferenciasTest.objects.update_or_create(
            postulante=postulante, defaults={**TEST_PRUEBA, 'fecha': timezone.now()})

        # Las postulaciones solo se crean la primera vez; si después cambias
        # su estado en el admin, volver a ejecutar el comando no lo pisa.
        for titulo, estado in POSTULACIONES_PRUEBA:
            oferta = OfertaTrabajo.objects.filter(titulo=titulo).first()
            if oferta is None:
                continue
            postulacion, nueva = Postulacion.objects.get_or_create(
                postulante=postulante, oferta=oferta)
            if nueva and estado != 'pendiente':
                # Se guarda aparte para que la señal cree el aviso de cambio de estado
                postulacion.estado = estado
                postulacion.save()

        self.stdout.write(self.style.SUCCESS(
            f"Usuario de prueba {'creado' if creado else 'actualizado'}: "
            f"usuario {USUARIO_PRUEBA['username']} (o {USUARIO_PRUEBA['email']}), "
            f"contraseña {USUARIO_PRUEBA['password']}"))
