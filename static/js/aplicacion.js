/* EventSpace — comportamiento comun de la interfaz */
document.addEventListener('DOMContentLoaded', function () {

  // ---- Menu lateral movil (con fondo oscuro, Esc y foco accesible) ----
  var sidebar = document.getElementById('sidebar');
  var backdrop = document.getElementById('sidebarBackdrop');
  var botones = document.querySelectorAll('[data-toggle-sidebar]');
  function abrirMenu(abrir) {
    if (!sidebar) return;
    sidebar.classList.toggle('abierto', abrir);
    if (backdrop) backdrop.classList.toggle('visible', abrir);
    botones.forEach(function (b) { b.setAttribute('aria-expanded', abrir ? 'true' : 'false'); });
    document.body.style.overflow = abrir ? 'hidden' : '';
  }
  botones.forEach(function (b) {
    b.addEventListener('click', function () { abrirMenu(!sidebar.classList.contains('abierto')); });
  });
  if (backdrop) backdrop.addEventListener('click', function () { abrirMenu(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('abierto')) { abrirMenu(false); }
  });

  // ---- Avisos: se cierran solos (menos los de error, para que se puedan leer) ----
  document.querySelectorAll('.alert:not(.alert-danger)').forEach(function (alerta) {
    setTimeout(function () {
      if (document.body.contains(alerta)) { bootstrap.Alert.getOrCreateInstance(alerta).close(); }
    }, 7000);
  });

  // ---- Mostrar / ocultar contrasena ----
  document.querySelectorAll('.login-card input[type="password"]').forEach(function (campo) {
    var envoltura = document.createElement('div');
    envoltura.className = 'pw-wrap';
    campo.parentNode.insertBefore(envoltura, campo);
    envoltura.appendChild(campo);
    var boton = document.createElement('button');
    boton.type = 'button';
    boton.className = 'pw-toggle';
    boton.setAttribute('aria-label', 'Mostrar contraseña');
    boton.setAttribute('aria-pressed', 'false');
    boton.innerHTML = '<i class="bi bi-eye" aria-hidden="true"></i>';
    boton.addEventListener('click', function () {
      var visible = campo.type === 'text';
      campo.type = visible ? 'password' : 'text';
      boton.setAttribute('aria-pressed', visible ? 'false' : 'true');
      boton.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
      boton.firstChild.className = visible ? 'bi bi-eye' : 'bi bi-eye-slash';
    });
    envoltura.appendChild(boton);
  });

  // ---- Landing: barra de navegacion con fondo al hacer scroll + revelado ----
  var nav = document.getElementById('lpNav');
  if (nav) {
    var alScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 24); };
    alScroll();
    window.addEventListener('scroll', alScroll, { passive: true });
    document.querySelectorAll('#lpMenu a[href^="#"]').forEach(function (a) {
      a.addEventListener('click', function () {
        var menu = document.getElementById('lpMenu');
        if (menu && menu.classList.contains('show')) { bootstrap.Collapse.getOrCreateInstance(menu).hide(); }
      });
    });
  }
  var revelar = document.querySelectorAll('.reveal');
  if (revelar.length) {
    if (!('IntersectionObserver' in window)) {
      revelar.forEach(function (el) { el.classList.add('visible'); });
    } else {
      var obs = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add('visible'); obs.unobserve(en.target); }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
      revelar.forEach(function (el) { obs.observe(el); });
    }
  }
});
