==========================================================================
 NexU - Trabajos y misiones cortas cerca de ti (Valparaíso / Viña del Mar)
==========================================================================

Versión de Django: el ramo pedía Django 5.1.1, pero esa versión NO es
compatible con Python 3.14. Por eso el proyecto usa Django 5.2 LTS
(5.2.8 o superior), que sí soporta Python 3.14. Ver requirements.txt.

En este PC el comando "python" no funciona. Usa "py".
Si "py" tampoco funciona, reemplázalo en TODOS los comandos por:
    C:\Users\elian\AppData\Local\Python\pythoncore-3.14-64\python.exe

--------------------------------------------------------------------------
 1. PRIMERA VEZ: INSTALAR Y PREPARAR
--------------------------------------------------------------------------
1) Descomprime el .zip en una carpeta, por ejemplo:
       C:\Users\elian\Documents\nexu
   Dentro de esa carpeta debe verse directamente el archivo manage.py.

2) Abre PowerShell en esa carpeta (en el Explorador: clic en la barra de
   direcciones, escribe "powershell" y Enter) o usa:
       cd C:\Users\elian\Documents\nexu

3) Instala las dependencias (solo Django):
       py -m pip install -r requirements.txt

4) Crea las migraciones y la base de datos (SQLite):
       py manage.py makemigrations cuentas empleos
       py manage.py migrate

5) Carga los datos de prueba (6 PyMEs, 32 ofertas y el usuario de
   prueba). Se puede repetir sin duplicar nada:
       py manage.py cargar_datos

   USUARIO DE PRUEBA (postulante normal, NO administrador):
       Usuario:     nexusprueba      (o el correo nexusprueba@nexu.cl)
       Contraseña:  nexus1234
   Ya tiene el test hecho y 2 postulaciones (una pendiente y una
   aceptada), así que al entrar ves recomendaciones y notificaciones.
   En la pantalla de inicio de sesión escribe "nexusprueba" en el campo
   "Correo o usuario".

6) Crea un administrador (para cambiar estados de postulaciones).
   IMPORTANTE: escribe un correo cuando te lo pida.
       py manage.py createsuperuser

7) Levanta el servidor:
       py manage.py runserver

8) Abre en el navegador (Chrome, Edge o Firefox):
       http://nexu.localhost:8000
   No hay que configurar nada: los navegadores envían *.localhost a tu
   propio PC y lo tratan como "seguro", así que la geolocalización funciona.
   También sirve http://127.0.0.1:8000

   Admin: http://nexu.localhost:8000/admin/

Para detener el servidor: Ctrl + C en la terminal.
Las veces siguientes solo necesitas el paso 7 (runserver).

Pruebas automáticas (opcional):
       py manage.py test

--------------------------------------------------------------------------
 2. OPCIONAL: USAR LA DIRECCIÓN http://nexu.usm
--------------------------------------------------------------------------
1) Abre el Bloc de notas COMO ADMINISTRADOR (clic derecho > Ejecutar como
   administrador).
2) Archivo > Abrir:  C:\Windows\System32\drivers\etc\hosts
   (en el selector de archivos elige "Todos los archivos" para verlo).
3) Agrega al final esta línea y guarda:
       127.0.0.1    nexu.usm
4) Levanta el servidor en el puerto 80 (si Windows lo pide, usa una
   terminal como administrador):
       py manage.py runserver 80
5) Abre http://nexu.usm
   (si prefieres no usar el puerto 80: "py manage.py runserver" y abre
   http://nexu.usm:8000)

OJO: con http://nexu.usm el navegador NO permite la geolocalización porque
no es HTTPS ni localhost (no es un "contexto seguro"). La app lo detecta y
muestra directamente el selector de comuna (Valparaíso, Viña del Mar,
Quilpué, Villa Alemana, Concón), que usa coordenadas de referencia.

--------------------------------------------------------------------------
 3. TELEGRAM (prioridad 2, opcional)
--------------------------------------------------------------------------
Sin configurar Telegram la app funciona igual; la opción aparece
deshabilitada en Configuraciones con una explicación.

Crear el bot con @BotFather:
1) En Telegram busca @BotFather (tiene un check azul) y presiona Iniciar.
2) Envía:  /newbot
3) Escribe el nombre visible, por ejemplo:  NexU Valpo
4) Escribe el nombre de usuario; debe terminar en "bot", por ejemplo:
       NexUValpoBot
5) BotFather responde con un TOKEN parecido a:
       123456789:AAH4k2Xy...  (no lo compartas ni lo subas a git)
6) (Opcional) Envía /setcommands, elige tu bot y pega:
       postulaciones - Ver mis postulaciones
       recomendados - Mis 5 trabajos más compatibles
       ayuda - Ver los comandos

Dónde poner el token:
1) En la carpeta nexu\ copia el archivo  config_local.ejemplo.py  y
   renombra la copia a  config_local.py
2) Ábrelo y completa:
       TELEGRAM_BOT_TOKEN = 'el token que te dio BotFather'
       TELEGRAM_BOT_USERNAME = 'NexUValpoBot'     (sin @)
3) config_local.py está en .gitignore, así que no se sube al repositorio.
4) Reinicia runserver para que tome la configuración.

Se necesitan DOS terminales abiertas en la carpeta del proyecto:
   Terminal 1:   py manage.py runserver
   Terminal 2:   py manage.py telegram_bot
El bot usa "long polling" (getUpdates): no necesita webhooks ni dominio
público, funciona en tu PC con internet. Ctrl + C lo detiene.

Comandos del bot:
   /start <código>  vincula la cuenta (se envía solo al usar el enlace)
   /postulaciones   lista tus postulaciones con PyME y estado
   /recomendados    tus 5 trabajos más compatibles (usa la comuna del perfil)
   /ayuda           explica los comandos

--------------------------------------------------------------------------
 3b. VERIFICACIÓN CON LINKEDIN (ofertas reales, no falsas)
--------------------------------------------------------------------------
Objetivo: que el postulante sepa si una oferta es real antes de postular.

Por qué no es automática: LinkedIn no tiene una API pública para consultar
ofertas de empleo. Su API de empleos es solo para socios aprobados por
LinkedIn (Talent Solutions), y leer sus páginas con un programa va contra
sus condiciones de uso. Por eso NexU usa una verificación manual:

1) Cada oferta puede tener el enlace a la MISMA oferta publicada en
   LinkedIn (campo "publicación en LinkedIn") y cada PyME el enlace a su
   página de empresa. NexU revisa que el enlace sea realmente de
   linkedin.com y lo deja en formato estándar. Acepta, por ejemplo:
       https://www.linkedin.com/jobs/view/1234567890/
       https://cl.linkedin.com/jobs/view/garzon-en-cafe-1234567890
       https://www.linkedin.com/jobs/search/?currentJobId=1234567890
2) El administrador abre el enlace (columna "LinkedIn" > Abrir), confirma
   que la publicación existe y es de esa PyME, y la marca como verificada
   (acción "Marcar como verificadas" o la casilla en la oferta).
3) El postulante ve el sello "Verificada en LinkedIn" en el mapa y en el
   detalle, puede abrir la publicación él mismo y puede filtrar con
   "Solo verificadas en LinkedIn".
Reglas: una oferta sin enlace no se puede verificar, y si se cambia el
enlace de una oferta verificada, pierde la verificación.

Las PyMEs de cargar_datos son ficticias, así que sus ofertas aparecen
"Sin verificar" (inventarles enlaces de LinkedIn sería justamente un dato
falso). Para la demo usa una publicación real (ver paso 9 del guion).

--------------------------------------------------------------------------
 4. CÓMO PROBAR TODO (guion para la demostración)
--------------------------------------------------------------------------
1) Test sin cuenta: en el login presiona "Haz el test de preferencias",
   responde las 6 preguntas y mira el resumen.
2) Crea una cuenta desde "Crear una cuenta". RUT de prueba válidos:
       11.111.111-1   22.222.222-2   19.876.543-0   20.123.456-5
   Al registrarte, el test que hiciste sin cuenta pasa a tu perfil.
   (Si no lo hiciste antes, se te invita a hacerlo, con opción de saltarlo.)
3) En el mapa presiona "Usar mi ubicación" y acepta el permiso (o elige
   una comuna). Verás tu punto, los círculos punteados de referencia y el
   círculo del radio. Los marcadores amarillos con estrella son los
   recomendados (70 % o más); los grises, el resto.
4) Abre "Filtros" (botón de líneas abajo a la derecha): mueve la distancia,
   marca jornadas o experiencia, o activa "Solo recomendados". El mapa se
   actualiza sin recargar.
5) Toca un marcador: verás pago, jornada, días, distancia y compatibilidad.
   Presiona "Postular": aparece "Postulaste a ..." y el popup cambia a
   "Ya postulaste". El sobre del encabezado muestra un punto rojo.
6) Endpoint JSON para la demo: en Filtros presiona "Ver estos resultados
   en JSON", o abre directamente, por ejemplo:
     http://nexu.localhost:8000/api/ofertas/?lat=-33.0245&lng=-71.5518&radio=3
     http://nexu.localhost:8000/api/ofertas/?lat=-33.0245&lng=-71.5518&radio=10&jornada=nocturna
     http://nexu.localhost:8000/api/ofertas/?lat=-33.0245&lng=-71.5518&radio=20&experiencia=sin&recomendados=1
   Cambia radio/jornada/experiencia en la URL y mira cómo cambian
   "total" y la lista (en la misma pestaña donde iniciaste sesión el
   JSON incluye tu puntaje).
7) Telegram: Configuraciones (engranaje) > "Conectar Telegram" > en
   Telegram presiona Iniciar. El bot responde "Tu cuenta NexU quedó
   conectada". Prueba /postulaciones y /recomendados.
8) Cambiar estado: entra a /admin/ con el superusuario > Postulaciones,
   cambia el estado a "Aceptada" en la lista y presiona Guardar. Llega
   el aviso por Telegram y aparece la notificación con punto rojo en la app.
9) Verificación con LinkedIn: busca cualquier oferta real en LinkedIn y
   copia su enlace. En /admin/ > Ofertas de trabajo, abre una oferta
   (ej. "Barista part-time"), pega el enlace en "publicación en LinkedIn"
   y guarda. En la app el detalle dice "Sin verificar" con el botón para
   abrirla. Vuelve al admin, selecciónala y usa la acción "Marcar como
   verificadas". Ahora el popup y el detalle muestran el sello verde y el
   filtro "Solo verificadas en LinkedIn" la muestra.
   En JSON: /api/ofertas/?lat=-33.0245&lng=-71.5518&radio=20&verificadas=1
10) Configuraciones también permite desactivar notificaciones, activar
   modo oscuro, guardar el idioma y repetir el test.

Nota: el superusuario no tiene perfil de postulante, así que no puede
postular. Para ver la app como usuario normal entra con nexusprueba /
nexus1234, o crea una cuenta nueva desde "Crear una cuenta" (útil para
mostrar el registro y la invitación al test).
Si alguna vez cambias la contraseña de nexusprueba y la olvidas, vuelve a
ejecutar "py manage.py cargar_datos" y queda otra vez en nexus1234.

--------------------------------------------------------------------------
 5. PROBLEMAS FRECUENTES
--------------------------------------------------------------------------
- "py no se reconoce": usa la ruta completa de python.exe indicada arriba.
- "no such table": faltó el paso 4 (makemigrations + migrate).
- El mapa sale gris: se necesita internet para los mapas de OpenStreetMap
  y Leaflet (se cargan desde cdnjs).
- El mapa muestra "Access blocked" / "403": OpenStreetMap exige que el
  navegador envíe el encabezado Referer. Ya está configurado
  (SECURE_REFERRER_POLICY en nexu/settings.py). Si lo seguías viendo,
  el navegador guardó las imágenes bloqueadas: recarga con Ctrl + F5 o
  prueba en una ventana de incógnito. Si aun así sigue bloqueado (puede
  pasar en algunas redes), cambia en nexu/settings.py:
      MAPA_PROVEEDOR = 'carto'
  y reinicia runserver. CARTO usa los mismos datos de OpenStreetMap,
  es gratis y no necesita API key.
- "Invalid HTTP_HOST header": abre la app con una de estas direcciones:
  127.0.0.1, localhost, nexu.localhost o nexu.usm.
- "La verificación CSRF ha fallado": la página tenía un token viejo
  (se usó Atrás después de iniciar sesión, o hay otra pestaña de NexU
  donde se inició/cerró sesión). La app ahora recarga la página sola con
  un aviso; solo vuelve a intentarlo. Si sigue pasando: cierra las otras
  pestañas de NexU, borra las cookies del sitio (o prueba en una ventana
  de incógnito) y no tengas otro proyecto Django corriendo al mismo tiempo
  en 127.0.0.1/localhost, porque comparten la cookie "csrftoken".
- Error "no such column: empleos_ofertatrabajo.linkedin_url" (o similar)
  después de actualizar: faltó migrar. Ejecuta:
      py manage.py makemigrations empleos
      py manage.py migrate
- El bot no responde: revisa que la terminal 2 esté corriendo, que el
  token sea correcto y que no haya otro programa usando el mismo bot.
