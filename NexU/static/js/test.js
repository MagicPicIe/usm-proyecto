/* Test de preferencias: muestra una pregunta por pantalla, con barra de
   progreso y botones Atrás / Siguiente. El envío final es un POST normal. */
(function () {
  'use strict';
  var form = document.getElementById('form-test');
  if (!form) return;

  var pasos = Array.prototype.slice.call(form.querySelectorAll('.pregunta'));
  var btnAtras = document.getElementById('btn-atras');
  var btnSiguiente = document.getElementById('btn-siguiente');
  var barra = document.querySelector('#progreso i');
  var progreso = document.getElementById('progreso');
  var numero = document.getElementById('paso-num');
  var actual = 0;

  function respondida(paso) {
    if (paso.dataset.tipo === 'rango') return true;
    return paso.querySelectorAll('input:checked').length > 0;
  }

  function actualizarBoton() {
    btnSiguiente.disabled = !respondida(pasos[actual]);
  }

  function mostrar(i) {
    actual = i;
    pasos.forEach(function (p, j) { p.classList.toggle('oculto', j !== i); });
    barra.style.width = ((i + 1) / pasos.length * 100) + '%';
    progreso.setAttribute('aria-valuenow', String(i + 1));
    numero.textContent = (i + 1) + ' de ' + pasos.length;
    btnAtras.style.visibility = i === 0 ? 'hidden' : 'visible';
    btnSiguiente.textContent = i === pasos.length - 1 ? 'Terminar test' : 'Siguiente';
    actualizarBoton();
    var titulo = pasos[i].querySelector('h1');
    if (titulo) { titulo.setAttribute('tabindex', '-1'); titulo.focus({ preventScroll: true }); }
    window.scrollTo(0, 0);
  }

  btnAtras.addEventListener('click', function () { if (actual > 0) mostrar(actual - 1); });

  btnSiguiente.addEventListener('click', function () {
    if (!respondida(pasos[actual])) return;
    if (actual === pasos.length - 1) form.submit();
    else mostrar(actual + 1);
  });

  form.addEventListener('change', function (e) {
    actualizarBoton();
    // En preguntas de una sola opción se avanza solo, como en una app
    if (e.target.type === 'radio' && actual < pasos.length - 1) {
      setTimeout(function () { mostrar(actual + 1); }, 220);
    }
  });

  var rango = document.getElementById('rango-distancia');
  var salida = document.getElementById('salida-distancia');
  rango.addEventListener('input', function () { salida.textContent = rango.value; });

  // Si el servidor devolvió errores, partir en la primera pregunta sin responder
  var primeraPendiente = pasos.findIndex(function (p) { return !respondida(p); });
  var hayErrores = document.querySelector('#mensajes-django [data-tipo="error"]');
  mostrar(hayErrores && primeraPendiente >= 0 ? primeraPendiente : 0);
})();
