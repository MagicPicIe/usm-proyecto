/* NexU – mapa principal.
   1) Obtiene la ubicación (GPS o comuna elegida).
   2) Dibuja el punto del usuario, círculos de referencia y el radio.
   3) Pide las ofertas al endpoint JSON con fetch cada vez que cambia un filtro.
   4) Muestra marcadores (recomendados en amarillo con estrella) y popups con Postular. */
(function () {
  'use strict';

  var cfg = JSON.parse(document.getElementById('config-mapa').textContent);
  var CLAVE_UBICACION = 'nexu-ubicacion';
  var REFERENCIAS_KM = [1, 2, 5, 10, 20];

  // --- Estado -------------------------------------------------------------
  var ubicacion = null;           // {lat, lng, origen}
  var ofertasPorId = {};          // cache de la última respuesta
  var marcadores = {};
  var controlador = null;         // AbortController para cancelar fetch viejos
  var temporizador = null;

  // --- Elementos ----------------------------------------------------------
  var $ = function (id) { return document.getElementById(id); };
  var fRadio = $('f-radio'), fRadioSalida = $('f-radio-salida'), fRecom = $('f-recomendados');
  var fVerif = $('f-verificadas');
  var panel = $('panel-filtros'), btnFiltros = $('btn-filtros');
  var chip = $('chip-resultados'), enlaceApi = $('enlace-api');
  var modal = $('modal-ubicacion');

  // --- Mapa base (Leaflet + OpenStreetMap, sin API key) ------------------
  var comunaInicial = cfg.comunas.find(function (c) { return c.codigo === cfg.comuna_perfil; }) || cfg.comunas[0];
  var mapa = L.map('mapa', { zoomControl: false }).setView([comunaInicial.lat, comunaInicial.lng], 13);
  L.control.zoom({ position: 'topleft' }).addTo(mapa);
  if (document.querySelector('.aviso-test')) document.body.classList.add('con-aviso-test');
  // Proveedores de mapas sin API key (se elige en settings.py: MAPA_PROVEEDOR)
  var ATRIBUCION_OSM = '&copy; colaboradores de <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
  var PROVEEDORES = {
    osm: {
      url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      opciones: { maxZoom: 19, attribution: ATRIBUCION_OSM }
    },
    carto: {
      url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      opciones: { maxZoom: 20, subdomains: 'abcd',
                  attribution: ATRIBUCION_OSM + ' &copy; <a href="https://carto.com/attributions">CARTO</a>' }
    }
  };
  var proveedor = PROVEEDORES[cfg.proveedor_mapa] || PROVEEDORES.osm;
  // referrerPolicy: cada imagen del mapa envía el origen como Referer, que
  // OpenStreetMap exige (si no, muestra "Access blocked").
  L.tileLayer(proveedor.url, Object.assign({ referrerPolicy: 'strict-origin-when-cross-origin' },
    proveedor.opciones)).addTo(mapa);

  var capaReferencia = L.layerGroup().addTo(mapa);
  var capaOfertas = L.layerGroup().addTo(mapa);
  var circuloRadio = null;

  // --- Filtros iniciales (precargados con el test si existe) -------------
  fRadio.value = cfg.filtros.radio;
  fRadioSalida.textContent = cfg.filtros.radio + ' km';
  document.querySelectorAll('input[name="jornada"]').forEach(function (c) {
    c.checked = cfg.filtros.jornada.indexOf(c.value) >= 0;
  });
  document.querySelectorAll('input[name="experiencia"]').forEach(function (c) {
    c.checked = cfg.filtros.experiencia.indexOf(c.value) >= 0;
  });
  fRecom.checked = !!cfg.filtros.recomendados;
  fVerif.checked = !!cfg.filtros.verificadas;

  function valoresMarcados(nombre) {
    return Array.prototype.map.call(
      document.querySelectorAll('input[name="' + nombre + '"]:checked'), function (c) { return c.value; });
  }

  // --- Utilidades ---------------------------------------------------------
  function escapar(texto) {
    return String(texto == null ? '' : texto).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  function formatoKm(km) {
    return km < 1 ? Math.round(km * 1000) + ' m' : km.toFixed(1).replace('.', ',') + ' km';
  }

  // Íconos SVG: recomendado (amarillo con estrella) o normal (gris azulado)
  function icono(recomendada) {
    var color = recomendada ? '#FFC531' : getComputedStyle(document.documentElement).getPropertyValue('--neutro-marcador').trim() || '#6B7A99';
    var centro = recomendada
      ? '<path d="M18 8.6l2.1 4.3 4.7.7-3.4 3.3.8 4.7-4.2-2.2-4.2 2.2.8-4.7-3.4-3.3 4.7-.7z" fill="#13203A"/>'
      : '<circle cx="18" cy="15" r="4.5" fill="#fff"/>';
    var tam = recomendada ? 44 : 34;
    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + tam + '" height="' + (tam * 1.22) + '" viewBox="0 0 36 44">' +
      '<path d="M18 1C9.2 1 2 8 2 16.6 2 28.3 18 43 18 43s16-14.7 16-26.4C34 8 26.8 1 18 1z" fill="' + color + '" stroke="#fff" stroke-width="2"/>' +
      centro + '</svg>';
    return L.divIcon({
      className: 'marcador', html: svg,
      iconSize: [tam, tam * 1.22], iconAnchor: [tam / 2, tam * 1.22], popupAnchor: [0, -tam * 1.1]
    });
  }

  function htmlPopup(o) {
    var compat = o.puntaje === null
      ? '<dt>Compatibilidad</dt><dd>Haz el test para verla</dd>'
      : '<dt>Compatibilidad</dt><dd>' + o.puntaje + ' %<div class="barra-compat"><i style="width:' + o.puntaje + '%"></i></div></dd>';
    var accion = o.ya_postulo
      ? '<span class="ya-postulaste"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5 9-10"/></svg>Ya postulaste</span>'
      : '<button type="button" class="btn btn-acento btn-postular" data-id="' + o.id + '">Postular</button>';
    // Verificación con LinkedIn: sello si NexU revisó la publicación
    var linkedin = o.verificada
      ? '<dt>LinkedIn</dt><dd class="txt-verificada">✓ Verificada</dd>'
      : '<dt>LinkedIn</dt><dd class="txt-sin-verificar">Sin verificar</dd>';
    var enlaceLinkedin = o.linkedin_url
      ? '<a class="enlace-externo" href="' + escapar(o.linkedin_url) + '" target="_blank" rel="noopener">Ver publicación en LinkedIn</a>'
      : '';
    return '<div class="popup-oferta">' +
      (o.recomendada ? '<span class="etiqueta-recomendada">★ Recomendado para ti</span> ' : '') +
      (o.verificada ? '<span class="etiqueta-verificada">✓ Verificada en LinkedIn</span>' : '') +
      '<h3>' + escapar(o.titulo) + '</h3>' +
      '<p class="pyme">' + escapar(o.pyme) + '</p>' +
      '<dl>' +
        '<dt>Pago</dt><dd>' + escapar(o.pago_texto) + '</dd>' +
        '<dt>Jornada</dt><dd>' + escapar(o.jornada_texto) + '</dd>' +
        '<dt>Días</dt><dd>' + escapar(o.dias_texto) + '</dd>' +
        '<dt>Distancia</dt><dd>' + formatoKm(o.distancia_km) + '</dd>' +
        compat + linkedin +
      '</dl>' +
      '<div class="popup-acciones">' +
        '<a class="btn btn-borde" href="' + escapar(o.url_detalle) + '">Ver detalle</a>' + accion +
      '</div>' + enlaceLinkedin + '</div>';
  }

  // --- Ubicación y referencias ----------------------------------------------
  function dibujarReferencias() {
    capaReferencia.clearLayers();
    var centro = [ubicacion.lat, ubicacion.lng];
    // Círculos concéntricos punteados (1, 2, 5, 10 y 20 km)
    REFERENCIAS_KM.forEach(function (km) {
      L.circle(centro, {
        radius: km * 1000, color: '#1846C9', weight: 1, opacity: .45,
        dashArray: '4 6', fill: false, interactive: false
      }).addTo(capaReferencia);
    });
    // Círculo del radio seleccionado
    circuloRadio = L.circle(centro, {
      radius: fRadio.value * 1000, color: '#1846C9', weight: 2,
      fillColor: '#1846C9', fillOpacity: .07, interactive: false
    }).addTo(capaReferencia);
    // Punto del usuario
    L.marker(centro, {
      icon: L.divIcon({ className: '', html: '<div class="marcador-usuario"></div>', iconSize: [20, 20], iconAnchor: [10, 10] }),
      title: 'Tu ubicación', keyboard: false, zIndexOffset: 1000
    }).addTo(capaReferencia).bindTooltip(ubicacion.origen === 'gps' ? 'Estás aquí' : 'Referencia: ' + ubicacion.origen);
  }

  function centrar() {
    if (!ubicacion || !circuloRadio) return;
    mapa.fitBounds(circuloRadio.getBounds(), { padding: [20, 20] });
  }

  function fijarUbicacion(lat, lng, origen) {
    ubicacion = { lat: lat, lng: lng, origen: origen };
    try { sessionStorage.setItem(CLAVE_UBICACION, JSON.stringify(ubicacion)); } catch (e) { /* */ }
    modal.classList.add('oculto');
    dibujarReferencias();
    centrar();
    cargarOfertas();
  }

  function mostrarComunas(motivo) {
    $('paso-gps').classList.add('oculto');
    $('paso-comuna').classList.remove('oculto');
    if (motivo) $('motivo-comuna').textContent = motivo;
  }

  function abrirModalUbicacion() {
    modal.classList.remove('oculto');
    $('paso-gps').classList.remove('oculto');
    $('paso-comuna').classList.add('oculto');
    // En http://nexu.usm (sin HTTPS) el navegador bloquea la geolocalización
    if (!window.isSecureContext || !('geolocation' in navigator)) {
      mostrarComunas('Tu navegador no permite usar la ubicación en esta dirección. Elige tu comuna y usaremos un punto de referencia.');
    }
  }

  // Lista de comunas con coordenadas de referencia
  cfg.comunas.forEach(function (c) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn btn-borde';
    b.textContent = c.nombre;
    b.addEventListener('click', function () { fijarUbicacion(c.lat, c.lng, c.nombre); });
    $('lista-comunas').appendChild(b);
  });

  $('btn-elegir-comuna').addEventListener('click', function () { mostrarComunas(); });

  $('btn-usar-ubicacion').addEventListener('click', function () {
    var btn = this;
    btn.disabled = true;
    btn.textContent = 'Buscando tu ubicación…';
    navigator.geolocation.getCurrentPosition(function (pos) {
      btn.disabled = false;
      btn.textContent = 'Usar mi ubicación';
      fijarUbicacion(pos.coords.latitude, pos.coords.longitude, 'gps');
    }, function (err) {
      btn.disabled = false;
      btn.textContent = 'Usar mi ubicación';
      var motivo = err.code === 1
        ? 'No diste permiso para usar tu ubicación. Elige tu comuna y usaremos un punto de referencia.'
        : 'No pudimos obtener tu ubicación. Elige tu comuna y usaremos un punto de referencia.';
      mostrarComunas(motivo);
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
  });

  $('btn-cambiar-ubicacion').addEventListener('click', function () {
    cerrarFiltros();
    abrirModalUbicacion();
  });

  $('btn-centrar').addEventListener('click', function () {
    if (ubicacion) centrar(); else abrirModalUbicacion();
  });

  // --- Ofertas ------------------------------------------------------------
  function urlApi() {
    var p = new URLSearchParams();
    p.set('lat', ubicacion.lat.toFixed(5));
    p.set('lng', ubicacion.lng.toFixed(5));
    p.set('radio', fRadio.value);
    var jornadas = valoresMarcados('jornada');
    var experiencias = valoresMarcados('experiencia');
    if (jornadas.length) p.set('jornada', jornadas.join(','));
    if (experiencias.length) p.set('experiencia', experiencias.join(','));
    if (fRecom.checked) p.set('recomendados', '1');
    if (fVerif.checked) p.set('verificadas', '1');
    return cfg.api + '?' + p.toString();
  }

  function cargarOfertas() {
    if (!ubicacion) return;
    var url = urlApi();
    enlaceApi.href = url;  // para la demostración: abrir el JSON en otra pestaña
    if (controlador) controlador.abort();
    controlador = new AbortController();
    chip.textContent = 'Buscando trabajos…';
    fetch(url, { signal: controlador.signal, credentials: 'same-origin', headers: { Accept: 'application/json' } })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(dibujarOfertas)
      .catch(function (e) {
        if (e.name === 'AbortError') return;
        chip.textContent = 'No se pudieron cargar los trabajos';
        NexU.aviso('No se pudieron cargar los trabajos. Revisa que el servidor siga corriendo.', 'error');
      });
  }

  function dibujarOfertas(datos) {
    capaOfertas.clearLayers();
    ofertasPorId = {};
    marcadores = {};
    // Se dibujan primero las normales y al final las recomendadas (quedan encima)
    var lista = datos.ofertas.slice().sort(function (a, b) { return (a.recomendada ? 1 : 0) - (b.recomendada ? 1 : 0); });
    lista.forEach(function (o) {
      ofertasPorId[o.id] = o;
      var m = L.marker([o.lat, o.lng], {
        icon: icono(o.recomendada), title: o.titulo, riseOnHover: true,
        zIndexOffset: o.recomendada ? 500 : 0
      });
      m.bindPopup(function () { return htmlPopup(ofertasPorId[o.id]); }, { maxWidth: 300 });
      m.addTo(capaOfertas);
      marcadores[o.id] = m;
    });
    var texto = datos.total === 0
      ? 'Sin trabajos con estos filtros. Prueba ampliar la distancia.'
      : datos.total + (datos.total === 1 ? ' trabajo' : ' trabajos');
    if (datos.test_realizado && datos.total > 0) {
      chip.innerHTML = escapar(texto) + ', <span class="estrella">★</span> ' + datos.total_recomendadas + ' recomendados';
    } else {
      chip.textContent = texto;
    }
  }

  // Postular desde el popup (POST con X-CSRFToken, ver app.js)
  mapa.on('popupopen', function (e) {
    var btn = e.popup.getElement().querySelector('.btn-postular');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var o = ofertasPorId[btn.dataset.id];
      btn.disabled = true;
      NexU.postular(o.url_postular).then(function (r) {
        if (r.ya_postulo) {
          o.ya_postulo = true;
          e.popup.setContent(htmlPopup(o));
        } else {
          btn.disabled = false;
        }
      });
    });
  });

  // --- Panel de filtros ---------------------------------------------------
  function abrirFiltros() {
    panel.classList.add('abierto');
    btnFiltros.classList.add('activo');
    btnFiltros.setAttribute('aria-expanded', 'true');
  }
  function cerrarFiltros() {
    panel.classList.remove('abierto');
    btnFiltros.classList.remove('activo');
    btnFiltros.setAttribute('aria-expanded', 'false');
  }
  btnFiltros.addEventListener('click', function () {
    if (panel.classList.contains('abierto')) cerrarFiltros(); else abrirFiltros();
  });
  $('btn-cerrar-filtros').addEventListener('click', cerrarFiltros);
  mapa.on('click', function () { if (window.innerWidth < 760) cerrarFiltros(); });

  // Cualquier cambio de filtro recarga los marcadores sin recargar la página
  function programarCarga() {
    clearTimeout(temporizador);
    temporizador = setTimeout(cargarOfertas, 250);
  }
  fRadio.addEventListener('input', function () {
    fRadioSalida.textContent = fRadio.value + ' km';
    if (circuloRadio) circuloRadio.setRadius(fRadio.value * 1000);
    programarCarga();
  });
  fRadio.addEventListener('change', centrar);
  panel.addEventListener('change', function (e) {
    if (e.target.type === 'checkbox') programarCarga();
  });

  // --- Inicio -------------------------------------------------------------
  var guardada = null;
  try { guardada = JSON.parse(sessionStorage.getItem(CLAVE_UBICACION) || 'null'); } catch (e) { /* */ }
  if (guardada && typeof guardada.lat === 'number') {
    fijarUbicacion(guardada.lat, guardada.lng, guardada.origen);
  } else {
    abrirModalUbicacion();
  }
})();
