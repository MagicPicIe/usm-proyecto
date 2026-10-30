
CATEGORIAS = [
    ('gastronomia', 'Gastronomía'),
    ('comercio', 'Comercio y ventas'),
    ('bodega', 'Bodega y logística'),
    ('reparto', 'Reparto'),
    ('atencion', 'Atención al cliente'),
    ('tutorias', 'Tutorías y educación'),
    ('tecnologia', 'Tecnología'),
    ('eventos', 'Eventos'),
    ('otros', 'Otros'),
]

JORNADAS = [
    ('diurna', 'Diurna'),
    ('nocturna', 'Nocturna'),
    ('un_dia', 'De un día'),
    ('part_time', 'Part-time'),
]

EXPERIENCIAS = [
    ('sin', 'Sin experiencia'),
    ('baja', 'Baja'),
    ('alta', 'Alta'),
]

DIAS = [
    ('lun', 'Lunes'),
    ('mar', 'Martes'),
    ('mie', 'Miércoles'),
    ('jue', 'Jueves'),
    ('vie', 'Viernes'),
    ('sab', 'Sábado'),
    ('dom', 'Domingo'),
]

ANIOS_CARRERA = [
    ('1', '1° año'),
    ('2', '2° año'),
    ('3', '3° año'),
    ('4', '4° año'),
    ('5', '5° año o más'),
]


CARRERAS = [
    ('civil', 'Ingeniería Civil'),
    ('ambiental', 'Ingeniería Civil Ambiental'),
    ('electrica', 'Ingeniería Civil Eléctrica'),
    ('electronica', 'Ingeniería Civil Electrónica'),
    ('industrial', 'Ingeniería Civil Industrial'),
    ('informatica', 'Ingeniería Civil Informática'),
    ('matematica', 'Ingeniería Civil Matemática'),
    ('mecanica', 'Ingeniería Civil Mecánica'),
    ('metalurgica', 'Ingeniería Civil Metalúrgica'),
    ('quimica', 'Ingeniería Civil Química'),
    ('telematica', 'Ingeniería Civil Telemática'),
    ('comercial', 'Ingeniería Comercial'),
    ('otra', 'Otra carrera'),
]

# Pago mínimo esperado por jornada/turno (CLP). 0 = sin mínimo.
RANGOS_PAGO = [
    (0, 'No tengo preferencia'),
    (15000, 'Desde $15.000'),
    (25000, 'Desde $25.000'),
    (35000, 'Desde $35.000'),
    (50000, 'Desde $50.000'),
]

COMUNAS = [
    ('valparaiso', 'Valparaíso'),
    ('vina', 'Viña del Mar'),
    ('quilpue', 'Quilpué'),
    ('villa_alemana', 'Villa Alemana'),
    ('concon', 'Concón'),
]

# Coordenadas de referencia (centro aproximado de cada comuna). Se usan cuando
# el navegador no entrega la ubicación.
COORDENADAS_COMUNAS = {
    'valparaiso': (-33.0472, -71.6127),
    'vina': (-33.0245, -71.5518),
    'quilpue': (-33.0472, -71.4425),
    'villa_alemana': (-33.0422, -71.3733),
    'concon': (-32.9300, -71.5190),
}


def etiqueta(opciones, codigo):
    """Devuelve el texto legible de un código ('un_dia' -> 'De un día')."""
    return dict(opciones).get(codigo, codigo)


def formatear_clp(monto):
    """15000 -> '$15.000' (formato chileno con punto de miles)."""
    return '$' + f'{int(monto):,}'.replace(',', '.')
