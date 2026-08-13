(function () {
  'use strict';

  function canonicalUrl() {
    var path = window.location.pathname.replace(/index\.html$/, '');
    return window.location.origin + path;
  }

  function refreshMetadata() {
    var url = canonicalUrl();
    document.querySelectorAll('link[rel="canonical"]').forEach(function (node) {
      node.setAttribute('href', url);
    });
    document.querySelectorAll('meta[property="og:url"]').forEach(function (node) {
      node.setAttribute('content', url);
    });
  }

  function ensureDailyEpochMenu() {
    var menu = document.getElementById('menu');
    if (!menu || menu.querySelector('.menu-item-dailyepoch')) return;

    var li = document.createElement('li');
    li.className = 'menu-item menu-item-dailyepoch';
    li.innerHTML = '<a href="/DailyEpoch/" rel="section">' +
      '<i class="menu-item-icon fa fa-fw fa-newspaper-o"></i><br>DailyEpoch</a>';

    var search = menu.querySelector('.menu-item-search');
    if (search) menu.insertBefore(li, search);
    else menu.appendChild(li);

    if (window.location.pathname.indexOf('/DailyEpoch/') === 0) {
      li.classList.add('menu-item-active');
    }
  }

  function refreshYear() {
    var year = String(new Date().getFullYear());
    document.querySelectorAll('[data-current-year], [itemprop="copyrightYear"]').forEach(function (node) {
      node.textContent = year;
    });
  }

  function hardenExternalLinks() {
    document.querySelectorAll('a[href^="http"]').forEach(function (link) {
      try {
        var url = new URL(link.href, window.location.href);
        if (url.origin !== window.location.origin) {
          link.setAttribute('target', '_blank');
          link.setAttribute('rel', 'noopener noreferrer');
        }
      } catch (_) {}
    });
  }

  function replaceCitationTokens() {
    var root = document.querySelector('.post-body');
    if (!root || !document.createTreeWalker) return;

    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    var pattern = /cite([^]+)/g;
    nodes.forEach(function (node) {
      if (!pattern.test(node.nodeValue)) {
        pattern.lastIndex = 0;
        return;
      }
      pattern.lastIndex = 0;
      var frag = document.createDocumentFragment();
      var text = node.nodeValue;
      var last = 0;
      var match;
      while ((match = pattern.exec(text))) {
        frag.appendChild(document.createTextNode(text.slice(last, match.index)));
        var sup = document.createElement('sup');
        sup.className = 'dailyepoch-source-ref';
        sup.textContent = '[来源]';
        sup.title = '原始检索引用标识：' + match[1].replace(//g, ', ');
        frag.appendChild(sup);
        last = pattern.lastIndex;
      }
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function installCopyButtons() {
    document.querySelectorAll('.post-body pre').forEach(function (pre) {
      if (pre.querySelector('.copy-code-button')) return;
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-code-button';
      button.textContent = '复制';
      button.addEventListener('click', function () {
        var code = pre.querySelector('code');
        var text = code ? code.innerText : pre.innerText;
        navigator.clipboard.writeText(text).then(function () {
          button.textContent = '已复制';
          window.setTimeout(function () { button.textContent = '复制'; }, 1200);
        }).catch(function () {
          button.textContent = '复制失败';
        });
      });
      pre.appendChild(button);
    });
  }

  function installBackToTop() {
    var button = document.querySelector('.back-to-top');
    if (!button) return;
    button.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    window.addEventListener('scroll', function () {
      button.style.display = window.scrollY > 240 ? 'block' : 'none';
    }, { passive: true });
  }

  function installMobileMenu() {
    var toggle = document.querySelector('.site-nav-toggle button');
    var nav = document.querySelector('.site-nav');
    if (!toggle || !nav || toggle.dataset.dailyepochBound) return;
    toggle.dataset.dailyepochBound = '1';
    toggle.addEventListener('click', function () {
      nav.classList.toggle('site-nav-on');
      nav.style.display = nav.classList.contains('site-nav-on') ? 'block' : '';
    });
  }

  function boot() {
    refreshMetadata();
    ensureDailyEpochMenu();
    refreshYear();
    hardenExternalLinks();
    replaceCitationTokens();
    installCopyButtons();
    installBackToTop();
    installMobileMenu();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
