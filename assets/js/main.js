/* Ферма «Рунская» — поведение сайта. Чистый JavaScript, без зависимостей. */
(function () {
  'use strict';

  var doc = document.documentElement;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* Год в подвале */
  $$('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });

  /* Шапка: состояние при прокрутке */
  var header = $('.header');
  function onScroll() {
    if (header) header.classList.toggle('is-scrolled', window.scrollY > 24);
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* Мобильное меню */
  var burger = $('.burger');
  var nav = $('#nav');
  function setMenu(open) {
    if (!header || !burger) return;
    header.classList.toggle('nav-open', open);
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    burger.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    doc.classList.toggle('no-scroll', open);
  }
  if (burger && nav) {
    burger.addEventListener('click', function () { setMenu(!header.classList.contains('nav-open')); });
    $$('a', nav).forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
    if (window.matchMedia) {
      var mq = window.matchMedia('(min-width: 1021px)');
      var onMq = function (e) { if (e.matches) setMenu(false); };
      if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq);
    }
  }

  /* Плавное появление блоков */
  var revealEls = $$('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.06 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* Мобильная плашка «Связаться»: показываем после первого экрана, прячем у формы */
  var dock = $('[data-dock]');
  var contacts = $('#contacts');
  if (dock) {
    var contactsVisible = false;
    var updateDock = function () {
      dock.classList.toggle('is-on', window.scrollY > window.innerHeight * 0.7 && !contactsVisible);
    };
    if (contacts && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (e) { contactsVisible = e[0].isIntersecting; updateDock(); }, { threshold: 0.12 }).observe(contacts);
    }
    window.addEventListener('scroll', updateDock, { passive: true });
    updateDock();
  }

  /* Форма: выбор продукции из ссылок и адресной строки */
  var form = $('#lead-form');
  var select = form ? $('select[name="product"]', form) : null;
  function setProduct(value) {
    if (!select || !value) return;
    select.value = value;
  }
  $$('[data-product]').forEach(function (a) {
    a.addEventListener('click', function () { setProduct(a.getAttribute('data-product')); });
  });
  try {
    var fromUrl = new URLSearchParams(window.location.search).get('product');
    if (fromUrl) setProduct(fromUrl);
  } catch (e) { /* старые браузеры */ }

  /* Форма: отправка */
  if (form) {
    var status = $('[data-status]', form);
    var email = form.getAttribute('data-email') || '';
    var phone = form.getAttribute('data-phone') || '';

    var say = function (kind, text, link) {
      status.className = 'form__status is-' + kind;
      status.textContent = text;
      if (link) {
        status.appendChild(document.createTextNode(' '));
        var a = document.createElement('a');
        a.href = link.href;
        a.textContent = link.label;
        status.appendChild(a);
      }
    };

    var fail = function (fd) {
      var link = null;
      var text = 'Не удалось отправить заявку автоматически.';
      if (email) {
        var body = 'Имя: ' + fd.get('name') + '\nКонтакт: ' + fd.get('contact') + '\nИнтересует: ' + (fd.get('product') || '—') + '\n\n' + (fd.get('message') || '');
        link = { href: 'mailto:' + email + '?subject=' + encodeURIComponent('Заявка с сайта фермы «Рунская»') + '&body=' + encodeURIComponent(body), label: 'Написать письмом' };
        text += ' Отправьте заявку письмом:';
      } else if (phone) {
        link = { href: 'tel:' + phone, label: phone };
        text += ' Позвоните нам:';
      } else {
        text += ' Пожалуйста, попробуйте чуть позже.';
      }
      say('error', text, link);
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.checkValidity()) { form.reportValidity(); return; }
      var fd = new FormData(form);
      form.classList.add('is-sending');
      say('ok', 'Отправляем…');
      fetch(form.getAttribute('data-endpoint') || 'send.php', { method: 'POST', body: fd, headers: { 'Accept': 'application/json' } })
        .then(function (r) {
          return r.json().then(function (j) { return { ok: r.ok, j: j }; });
        })
        .then(function (res) {
          form.classList.remove('is-sending');
          if (res.ok && res.j && res.j.ok) {
            form.reset();
            say('ok', 'Спасибо! Заявка отправлена — мы свяжемся с вами.');
          } else {
            fail(fd);
          }
        })
        .catch(function () {
          form.classList.remove('is-sending');
          fail(fd);
        });
    });
  }

  /* Журнал: фильтр по темам и поиск */
  var grid = $('#article-grid');
  if (grid) {
    var cards = $$('.card', grid);
    var filters = $$('.filter');
    var search = $('#article-search');
    var counter = $('[data-count]');
    var empty = $('.library__empty');
    var category = 'all';
    var query = '';
    var apply = function () {
      var shown = 0;
      cards.forEach(function (c) {
        var ok = (category === 'all' || c.getAttribute('data-category') === category) &&
                 (!query || (c.getAttribute('data-search') || '').indexOf(query) !== -1);
        c.hidden = !ok;
        if (ok) shown++;
      });
      if (counter) counter.textContent = shown;
      if (empty) empty.hidden = shown !== 0;
    };
    filters.forEach(function (b) {
      b.addEventListener('click', function () {
        category = b.getAttribute('data-filter');
        filters.forEach(function (x) { x.classList.toggle('is-active', x === b); });
        apply();
      });
    });
    if (search) {
      search.addEventListener('input', function () { query = search.value.trim().toLowerCase(); apply(); });
    }
  }
})();
