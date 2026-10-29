/* NexU – utilidades compartidas: CSRF, avisos flotantes, paneles,
   modo oscuro, notificaciones y postular. */
(function () {
  'use strict';

  // --- Token CSRF (Django lo exige en todo POST) ---------------------------
  function obtenerCsrf() {
    var campo = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (campo) return campo.value;
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function enviarPost(url, datos) {
    return fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': obtenerCsrf(),
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams(datos || {}).toString(),
      credentials: 'same-origin'
    }).then(function (r) {
      return r.json().catch(function () { return { ok: false, mensaje: 'Respuesta inesperada del servidor.' }; });
    });
  }

  // --- Avisos flotantes ------------------------------------------------------
  function aviso(texto, tipo) {
    var cont = document.getElementById('avisos');
    if (!cont) return;
    var div = document.createElement('div');
    div.className = 'aviso' + (tipo === 'error' ? ' error' : '');
    div.textContent = texto;
    cont.appendChild(div);
    setTimeout(function () { div.remove(); }, 3800);
  }

  // --- Postular (detalle y popups del mapa) -------------------------------
  function postular(url) {
    return enviarPost(url).then(function (r) {
      aviso(r.mensaje || 'No se pudo postular.', r.ok ? 'ok' : 'error');
      return r;
    }).catch(function () {
      aviso('No se pudo conectar con el servidor. Revisa tu conexión.', 'error');
      return { ok: false };
    });
  }

  window.NexU = { csrf: obtenerCsrf, post: enviarPost, aviso: aviso, postular: postular };

  // Mensajes de Django -> avisos
  document.querySelectorAll('#mensajes-django li').forEach(function (li) {
    aviso(li.textContent, li.dataset.tipo);
  });

  // Botón Postular de la página de detalle
  document.querySelectorAll('[data-postular]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.disabled = true;
      postular(btn.dataset.postular).then(function (r) {
        if (r.ya_postulo) {
          btn.textContent = 'Ya postulaste';
          btn.className = 'btn btn-borde';
        } else {
          btn.disabled = false;
        }
      });
    });
  });

  // --- Mostrar / ocultar contraseña -----------------------------------------
  document.querySelectorAll('.ver-password').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = btn.parentElement.querySelector('input');
      var mostrar = input.type === 'password';
      input.type = mostrar ? 'text' : 'password';
      btn.setAttribute('aria-pressed', String(mostrar));
      btn.setAttribute('aria-label', mostrar ? 'Ocultar contraseña' : 'Mostrar contraseña');
      btn.querySelector('.ojo-abierto').classList.toggle('oculto', mostrar);
      btn.querySelector('.ojo-cerrado').classList.toggle('oculto', !mostrar);
    });
  });

  // --- Paneles del encabezado (notificaciones y configuraciones) -----------
  var botonesPanel = document.querySelectorAll('[data-abre]');
  function cerrarPaneles(excepto) {
    botonesPanel.forEach(function (b) {
      var panel = document.getElementById(b.dataset.abre);
      if (panel && panel !== excepto) {
        panel.classList.add('oculto');
        b.setAttribute('aria-expanded', 'false');
      }
    });
  }
  botonesPanel.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var panel = document.getElementById(btn.dataset.abre);
      var abrir = panel.classList.contains('oculto');
      cerrarPaneles(panel);
      panel.classList.toggle('oculto', !abrir);
      btn.setAttribute('aria-expanded', String(abrir));

      // Al abrir las notificaciones se marcan como leídas
      if (abrir && btn.dataset.sinLeer) {
        enviarPost(btn.dataset.marcarUrl).then(function () {
          delete btn.dataset.sinLeer;
          var punto = document.getElementById('punto-rojo');
          if (punto) punto.remove();
          btn.setAttribute('aria-label', 'Notificaciones');
        });
      }
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.panel-flotante')) cerrarPaneles(null);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') cerrarPaneles(null);
  });

  // --- Modo oscuro (guardado en localStorage) ----------------------------
  var swTema = document.getElementById('cfg-tema');
  if (swTema) {
    swTema.checked = document.documentElement.getAttribute('data-theme') === 'dark';
    swTema.addEventListener('change', function () {
      var tema = swTema.checked ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', tema);
      try { localStorage.setItem('nexu-tema', tema); } catch (err) { /* modo privado */ }
    });
  }

  // --- Idioma (solo guarda la preferencia) -------------------------------
  var selIdioma = document.getElementById('cfg-idioma');
  if (selIdioma) {
    try { selIdioma.value = localStorage.getItem('nexu-idioma') || 'es'; } catch (err) { /* */ }
    selIdioma.addEventListener('change', function () {
      try { localStorage.setItem('nexu-idioma', selIdioma.value); } catch (err) { /* */ }
      aviso('Preferencia de idioma guardada');
    });
  }

  // --- Notificaciones activadas / desactivadas ---------------------------
  var swNotif = document.getElementById('cfg-notificaciones');
  if (swNotif && !swNotif.disabled) {
    swNotif.addEventListener('change', function () {
      enviarPost(swNotif.dataset.url, { activas: swNotif.checked ? '1' : '0' }).then(function (r) {
        if (r.ok) aviso(r.mensaje);
        else { swNotif.checked = !swNotif.checked; aviso(r.mensaje || 'No se pudo guardar.', 'error'); }
      });
    });
  }
})();
