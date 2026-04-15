document.addEventListener('DOMContentLoaded', function () {
  var app = document.getElementById('admin-app');
  if (!app) return;

  var cfg = window.__DASHBOARD_CONFIG__ || {};
  var urls = Object.assign({
    dashboardAdmin: '/dashboard/admin/',
    dashboardSeller: '/dashboard/seller/',
    storeList: '#',
    transactionList: '/dashboard/orders/',
    productManage: '/dashboard/products/',
    productCreate: '/dashboard/products/create/',
    categoryList: '/dashboard/categories/',
    myStore: '/dashboard/my-store/',
    storeAddress: '/dashboard/my-store/address/',
    storePaymentMethod: '/dashboard/my-store/payment-method/',
    orderList: '/dashboard/orders/',
    salesReportSeller: '/dashboard/sales-report/',
    reportSales: '/dashboard/reports/sales/',
    userList: '/dashboard/users/',
    productReviews: '/dashboard/product-reviews/',
    settings: '#',
    manageKonten: '#',
    logout: '/auth/logout/',
    home: '/'
  }, cfg.urls || {});
  var pageTitle = cfg.pageTitle || app.getAttribute('data-page-title') || 'Dashboard';
  var role = (cfg.role || app.getAttribute('data-role') || 'admin').trim().toLowerCase();
  var storeProfileComplete = cfg.storeProfileComplete !== false;  // Default to true for non-sellers
  var mainContent = app.innerHTML;
  var currentPath = window.location.pathname || '/';
  var currentPage = (window.location.pathname.split('/').filter(Boolean).pop() || 'index').toLowerCase();
  var activePageTitle = pageTitle;
  var activePath = currentPath;
  var activePageSlug = currentPage;
  var sweetAlertJsPath = (cfg.staticVendor || '/static/dashboard/assets/vendor/') + 'sweetalert2/sweetalert2.min.js';
  var sweetAlertCssPath = (cfg.staticVendor || '/static/dashboard/assets/vendor/') + 'sweetalert2/sweetalert2.min.css';

  function ensureSweetAlertReady() {
    if (window.Swal) return Promise.resolve();
    if (window.__swalReadyPromise) return window.__swalReadyPromise;

    var cssExists = document.querySelector('link[data-swal-local="1"]');
    if (!cssExists) {
      var swalCss = document.createElement('link');
      swalCss.rel = 'stylesheet';
      swalCss.href = sweetAlertCssPath;
      swalCss.setAttribute('data-swal-local', '1');
      document.head.appendChild(swalCss);
    }

    window.__swalReadyPromise = new Promise(function (resolve) {
      var script = document.createElement('script');
      script.src = sweetAlertJsPath;
      script.async = true;
      script.onload = function () { resolve(); };
      script.onerror = function () { resolve(); };
      document.body.appendChild(script);
    });

    return window.__swalReadyPromise;
  }

  function normalizeToastLevel(level) {
    var safeLevel = String(level || '').toLowerCase();
    if (safeLevel.indexOf('error') !== -1 || safeLevel.indexOf('danger') !== -1) return 'error';
    if (safeLevel.indexOf('warning') !== -1) return 'warning';
    if (safeLevel.indexOf('success') !== -1) return 'success';
    return 'info';
  }

  function showDjangoToastsFromWindow() {
    var queue = Array.isArray(window.__DJANGO_MESSAGES__) ? window.__DJANGO_MESSAGES__.slice() : [];
    if (!queue.length) return;

    // Consume once so soft navigation won't replay old messages.
    window.__DJANGO_MESSAGES__ = [];

    ensureSweetAlertReady().then(function () {
      if (!window.Swal) return;
      queue.forEach(function (msg, idx) {
        setTimeout(function () {
          window.Swal.fire({
            toast: true,
            position: 'top-end',
            icon: normalizeToastLevel(msg.level),
            title: msg.text || '',
            showConfirmButton: false,
            timer: 2600,
            timerProgressBar: true
          });
        }, idx * 180);
      });
    });
  }

  /* ── Sidebar menu items ─────────────────────────────────── */
  var menuItems = [
    {
      label: 'Dashboard',
      href: role === 'admin' ? (urls.dashboardAdmin || '#') : (urls.dashboardSeller || '#'),
      iconDefault: 'home-black.svg',
      iconActive: 'home-blue-fill.svg',
      type: 'link',
      visibleFor: ['admin', 'seller'],
      activePages: ['Dashboard'],
      relatedPaths: ['/dashboard/admin/', '/dashboard/seller/']
    },
    {
      label: 'Manage Store',
      iconDefault: 'bag-2-black.svg',
      type: 'accordion',
      id: 'acc-store',
      children: [
        {
          label: 'List Store',
          href: urls.storeList || '#',
          iconDefault: 'shop-grey.svg',
          iconActive: 'shop-blue-fill.svg',
          visibleFor: ['admin'],
          activePages: ['Store List', 'Store Create', 'Store Edit', 'Store Detail']
        },
        {
          label: 'List Transaction',
          href: urls.transactionList || '#',
          iconDefault: 'stickynote-grey.svg',
          iconActive: 'stickynote-blue-fill.svg',
          visibleFor: ['admin'],
          activePages: ['Transactions', 'Transaction Detail']
        },
        {
          label: 'Profile',
          href: urls.myStore || '#',
          iconDefault: 'shop-grey.svg',
          iconActive: 'shop-blue-fill.svg',
          visibleFor: ['seller'],
          activePages: ['My Store', 'Store Profile']
        },
        {
          label: 'Alamat Toko',
          href: urls.storeAddress || '#',
          iconDefault: 'shop-grey.svg',
          iconActive: 'shop-blue-fill.svg',
          visibleFor: ['seller'],
          activePages: ['Store Address']
        },
        {
          label: 'Payment',
          href: urls.storePaymentMethod || '#',
          iconDefault: 'wallet-grey.svg',
          iconActive: 'wallet-blue-fill.svg',
          visibleFor: ['seller'],
          activePages: ['Payment Method']
        }
      ]
    },
    {
      label: 'Manage Product',
      iconDefault: 'box-black.svg',
      type: 'accordion',
      id: 'acc-product',
      requiresCompleteProfile: true,
      children: [
        {
          label: 'Categories',
          href: urls.categoryList || '#',
          iconDefault: 'bag-grey.svg',
          iconActive: 'bag-blue-fill.svg',
          visibleFor: ['admin'],
          activePages: ['Categories', 'Category Create', 'Category Edit', 'Category Detail']
        },
        {
          label: 'Products',
          href: urls.productManage || '#',
          iconDefault: 'bag-grey.svg',
          iconActive: 'bag-blue-fill.svg',
          visibleFor: ['admin', 'seller'],
          activePages: ['Products', 'Product List', 'Product Create', 'Product Detail', 'Product Edit'],
          relatedPaths: ['/dashboard/products/', '/dashboard/products/create/']
        }
      ]
    },
    {
      label: 'Manage Orders',
      href: urls.orderList || '#',
      iconDefault: 'stickynote-grey.svg',
      iconActive: 'stickynote-blue-fill.svg',
      type: 'link',
      visibleFor: ['seller'],
      requiresCompleteProfile: true,
      activePages: ['Manage Orders', 'Transaction Detail']
    },
    {
      label: 'Sales Report',
      href: urls.salesReportSeller || '#',
      iconDefault: 'presention-chart-grey.svg',
      iconActive: 'presention-chart-blue.svg',
      type: 'link',
      visibleFor: ['seller'],
      requiresCompleteProfile: true,
      activePages: ['Sales Report']
    },
    {
      label: 'Manage Users',
      href: urls.userList || '#',
      iconDefault: 'profile-2user-black.svg',
      iconActive: 'profile-2user-blue-fill.svg',
      type: 'link',
      visibleFor: ['admin'],
      activePages: ['Users']
    },
    {
      label: 'Product Reviews',
      href: urls.productReviews || '#',
      iconDefault: 'star-grey.svg',
      iconActive: 'star-blue-fill.svg',
      type: 'link',
      visibleFor: ['seller'],
      requiresCompleteProfile: true,
      activePages: ['Reviews', 'Product Reviews']
    },
    {
      label: 'Settings',
      href: urls.settings || '#',
      iconDefault: 'setting-2-grey.svg',
      iconActive: 'setting-2-grey.svg',
      type: 'link',
      visibleFor: ['admin'],
      activePages: ['Settings']
    },
    {
      label: 'Manage Konten',
      href: urls.manageKonten || '#',
      iconDefault: 'map-grey.svg',
      iconActive: 'map-blue-fill.svg',
      type: 'link',
      visibleFor: ['admin'],
      activePages: ['Settings']
    }
  ];

  /* ── Helpers ─────────────────────────────────────────────── */
  function normalizePath(path) {
    if (!path) return '/';
    var clean = path.split('?')[0].split('#')[0];
    if (clean.length > 1 && clean.endsWith('/')) clean = clean.slice(0, -1);
    return clean || '/';
  }

  function extractPath(url) {
    if (!url) return '';
    if (url.indexOf('http://') === 0 || url.indexOf('https://') === 0) {
      try {
        return new URL(url).pathname;
      } catch (e) {
        return url;
      }
    }
    return url;
  }

  function isPageActive(item) {
    if (item.href && item.href !== '#') {
      if (normalizePath(extractPath(item.href)) === normalizePath(activePath)) return true;
    }
    if (item.relatedPaths && item.relatedPaths.some(function (path) { return normalizePath(path) === normalizePath(activePath); })) return true;
    if (item.relatedPages && item.relatedPages.indexOf(activePageSlug) !== -1) return true;
    if (item.activePages && item.activePages.indexOf(activePageTitle) !== -1) return true;
    return false;
  }

  function isVisible(item) {
    if (!item.visibleFor) return true;
    return item.visibleFor.map(function(v) { return v.trim().toLowerCase(); }).indexOf(role) !== -1;
  }

  function iconPath(name) {
    return (cfg.staticIcons || '/static/dashboard/assets/images/icons/') + name;
  }

  function logoPath(name) {
    return (cfg.staticLogos || '/static/dashboard/assets/images/logos/') + name;
  }

  /* ── Build sidebar items ─────────────────────────────────── */
  function buildSidebarItem(item) {
    var active = isPageActive(item);
    var activePages = (item.activePages || []).join('||');
    var relatedPages = (item.relatedPages || []).join('||');
    var relatedPaths = (item.relatedPaths || []).join('||');
    var isDisabled = role === 'seller' && item.requiresCompleteProfile && !storeProfileComplete;
    var disabledClass = isDisabled ? ' opacity-50 pointer-events-none' : '';
    var disabledAttr = isDisabled ? ' onclick="return false;" title="Lengkapi profil toko terlebih dahulu"' : '';
    
    return '<li>' +
      '<a href="' + (isDisabled ? '#' : item.href) + '" data-sidebar-link="1" data-active-pages="' + activePages + '" data-related-pages="' + relatedPages + '" data-related-paths="' + relatedPaths + '" class="sidebar-item' + (active ? ' active' : '') + disabledClass + ' flex items-center w-full min-h-[50px] gap-4 rounded-xl overflow-hidden py-3 pl-5 pr-3 transition-300 hover:bg-gray-50"' + disabledAttr + '>' +
        '<div class="relative flex size-[22px] shrink-0">' +
          '<img src="' + iconPath(item.iconDefault) + '" class="icon-default size-[22px] absolute opacity-100 transition-300" alt="">' +
          '<img src="' + iconPath(item.iconActive) + '" class="icon-active size-[22px] absolute opacity-0 transition-300" alt="">' +
        '</div>' +
        '<p class="sidebar-label font-medium text-[15px] transition-300 w-full">' + item.label + '</p>' +
        '<div class="active-bar w-[3px] h-9 shrink-0 rounded-l-lg bg-custom-blue hidden transition-300"></div>' +
      '</a>' +
    '</li>';
  }

  function buildAccordion(item) {
    var visibleChildren = item.children.filter(isVisible);
    if (visibleChildren.length === 0) return '';

    var hasActiveChild = visibleChildren.some(isPageActive);
    var isOpen = hasActiveChild;
    var isDisabled = role === 'seller' && item.requiresCompleteProfile && !storeProfileComplete;
    var disabledClass = isDisabled ? ' opacity-50 pointer-events-none' : '';
    var disabledAttr = isDisabled ? ' onclick="return false;" title="Lengkapi profil toko terlebih dahulu"' : '';

    var branchLines = visibleChildren.length > 0 ? '<div class="branch-line"></div>' : '';

    var childrenHtml = '';
    visibleChildren.forEach(function (child) {
      if (!isVisible(child)) return; 
      var active = isPageActive(child);
      var childActivePages = (child.activePages || []).join('||');
      var childRelatedPages = (child.relatedPages || []).join('||');
      var childRelatedPaths = (child.relatedPaths || []).join('||');
      childrenHtml += '<li class="relative">' +
        '<div class="curve-branch"></div>' +
        '<a href="' + child.href + '" data-sidebar-link="1" data-active-pages="' + childActivePages + '" data-related-pages="' + childRelatedPages + '" data-related-paths="' + childRelatedPaths + '" class="sidebar-item' + (active ? ' active' : '') + ' flex items-center w-full min-h-[50px] gap-4 rounded-xl overflow-hidden py-3 pl-5 pr-3 transition-300 hover:bg-gray-50">' +
          '<div class="relative flex size-[22px] shrink-0">' +
            '<img src="' + iconPath(child.iconDefault) + '" class="icon-default size-[22px] absolute opacity-100 transition-300" alt="">' +
            '<img src="' + iconPath(child.iconActive) + '" class="icon-active size-[22px] absolute opacity-0 transition-300" alt="">' +
          '</div>' +
          '<p class="sidebar-label font-medium text-[15px] text-custom-grey transition-300 w-full">' + child.label + '</p>' +
          '<div class="active-bar w-[3px] h-9 shrink-0 rounded-l-lg bg-custom-blue hidden transition-300"></div>' +
        '</a>' +
      '</li>';
    });

    return '<li class="flex flex-col">' +
      '<button data-accordion-id="' + item.id + '" onclick="' + (isDisabled ? 'return false;' : 'toggleAccordion(\'' + item.id + '\');') + '" class="flex items-center w-full min-h-[50px] gap-4 rounded-xl overflow-hidden py-3 pl-5 pr-3 transition-300 hover:bg-gray-50' + disabledClass + '"' + disabledAttr + '>' +
        '<div class="relative flex size-[22px] shrink-0">' +
          '<img src="' + iconPath(item.iconDefault) + '" class="size-[22px]" alt="">' +
        '</div>' +
        '<p class="font-medium text-[15px] transition-300 w-full text-left">' + item.label + '</p>' +
        '<svg id="' + item.id + '-arrow" class="size-5 shrink-0 mr-1 transition-300 text-gray-400' + (isOpen && !isDisabled ? ' rotate-90' : '') + '" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m9 18 6-6-6-6"/></svg>' +
      '</button>' +
      '<div id="' + item.id + '"' + (isOpen && !isDisabled ? '' : ' class="hidden"') + '>' +
        '<div class="flex">' +
          '<div class="flex w-[52px] shrink-0 justify-end items-start relative">' + branchLines + '</div>' +
          '<ul class="flex flex-col gap-1 w-full">' + childrenHtml + '</ul>' +
        '</div>' +
      '</div>' +
    '</li>';
  }

  /* ── Build sidebar menu ──────────────────────────────────── */
  var sidebarMenuHtml = '';
  menuItems.forEach(function (item) {
    if (!isVisible(item)) return;
    
    if (item.type === 'link') {
      sidebarMenuHtml += buildSidebarItem(item);
    } else if (item.type === 'accordion') {
      // Filter children here to ensure accuracy
      var originalChildren = item.children;
      item.children = item.children.filter(isVisible);
      
      if (item.children.length > 0) {
        sidebarMenuHtml += buildAccordion(item);
      }
      
      // Restore original children for next potential use
      item.children = originalChildren;
    }
  });

  var roleName = cfg.userRoleDisplay || (role === 'admin' ? 'Administrator' : 'Seller');
  var userName = cfg.userName || 'User';
  var userAvatar = cfg.userAvatar || iconPath('photo-profile-default.svg');
  var logoutUrl = urls.logout || '#';
  var homeUrl = urls.home || '/';

  /* ── Inline SVG icons for the navbar ─────────────────────── */
  var svgHamburger = '<svg class="size-7" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path stroke-linecap="round" d="M4 6h16M4 12h16M4 18h16"/></svg>';
  var svgBell = '<svg class="size-[22px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>';
  var svgGlobe = '<svg class="size-[22px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z"/></svg>';
  var svgSun = '<svg class="size-[22px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
  var svgGrid = '<svg class="size-[22px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>';
  var svgChevron = '<svg class="size-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m19 9-7 7-7-7"/></svg>';
  var svgUser = '<svg class="size-[18px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
  var svgSettings = '<svg class="size-[18px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>';
  var svgLogout = '<svg class="size-[18px] text-gray-500" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>';
  var svgClose = '<svg class="size-7" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" d="M18 6 6 18M6 6l12 12"/></svg>';
  var svgCollapseLeft = '<svg class="size-4" fill="none" stroke="white" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="m15 18-6-6 6-6"/></svg>';

  /* ── LAYOUT HTML ─────────────────────────────────────────── */
  var layoutHtml = '' +

  /* Overlay for mobile sidebar */
  '<div id="sidebar-overlay" class="fixed inset-0 bg-black/40 z-40 hidden lg:hidden transition-300" onclick="closeSidebar()"></div>' +

  /* SIDEBAR */
  '<aside id="sidebar" class="fixed top-0 left-0 z-50 flex flex-col w-[280px] h-screen bg-white border-r border-gray-100 transition-300 -translate-x-full lg:translate-x-0 lg:z-30">' +
    /* Logo area */
    '<div class="flex items-center justify-between h-[76px] px-6 shrink-0">' +
      '<a href="' + homeUrl + '" class="flex items-center gap-2">' +
        '<img src="' + logoPath('logokopmas.png') + '" class="h-12 w-auto" alt="Kopmas Shop">' +
      '</a>' +
      /* Close button (mobile) */
      '<button onclick="closeSidebar()" class="lg:hidden flex items-center justify-center size-9 rounded-full hover:bg-gray-100 transition-300 text-gray-500">' + svgClose + '</button>' +
    '</div>' +
    /* Menu */
    '<div class="flex flex-col flex-1 overflow-y-auto hide-scrollbar px-5 py-6">' +
      '<p class="text-[11px] font-bold uppercase tracking-widest text-custom-grey/60 mb-4 pl-5">Main Menu</p>' +
      '<ul class="flex flex-col gap-1.5">' + sidebarMenuHtml + '</ul>' +
    '</div>' +
  '</aside>' +

  /* MAIN WRAPPER (pushed right by sidebar on desktop) */
  '<div id="main-wrapper" class="flex flex-col flex-1 min-w-0 lg:ml-[280px] transition-300">' +

    /* FLOATING TOP NAVBAR */
    '<div class="sticky top-0 z-30 px-4 lg:px-6 pt-4 lg:pt-5 pb-2 bg-custom-background">' +
    '<header id="top-navbar" class="flex items-center h-16 bg-white shadow-[0_2px_12px_rgba(0,0,0,0.08)] rounded-2xl px-4 lg:px-6 gap-4" style="height:64px">' +
      /* Hamburger (mobile) */
      '<button id="btn-hamburger" onclick="openSidebar()" class="lg:hidden flex items-center justify-center size-11 rounded-xl hover:bg-gray-100 transition-300 text-gray-600 shrink-0">' + svgHamburger + '</button>' +
      '<div class="flex-1 min-w-0 flex items-center gap-3">' +
        '<div class="min-w-0 hidden sm:flex flex-col">' +
          '<p class="text-[11px] tracking-wide uppercase text-custom-grey">Current Page</p>' +
            '<p id="navbar-current-page" class="text-[15px] font-semibold text-custom-black truncate">' + pageTitle + '</p>' +
        '</div>' +
      '</div>' +
      /* Navbar icons */
      '<div class="flex items-center gap-2 sm:gap-3">' +
        '<div class="relative">' +
          '<button id="notif-btn" onclick="toggleNotificationDropdown(event)" class="relative flex items-center justify-center size-11 rounded-xl hover:bg-gray-100 transition-300">' +
            svgBell +
            '<span id="notif-badge" class="absolute top-2 right-2 flex size-2 rounded-full bg-red-500 ring-2 ring-white"></span>' +
          '</button>' +
          '<div id="notif-dropdown" class="hidden absolute right-0 top-full mt-3 w-[calc(100vw-2rem)] sm:w-[380px] bg-white rounded-xl shadow-xl ring-1 ring-gray-100 overflow-hidden z-50">' +
            '<div class="flex items-center justify-between px-4 py-3 border-b border-gray-100">' +
              '<div class="flex items-center gap-2">' +
                '<img src="' + logoPath('notification-black.svg') + '" class="size-5" alt="Notifikasi">' +
                '<p class="font-semibold text-[15px] text-custom-black">Notifikasi</p>' +
              '</div>' +
              '<button onclick="clearNotifications(event)" class="text-[12px] font-semibold text-custom-blue hover:underline">Hapus Semua</button>' +
            '</div>' +
            '<p id="notif-count" class="px-4 pt-2 pb-3 text-xs text-custom-grey">4 notifikasi terbaru</p>' +
            '<div class="max-h-[360px] overflow-y-auto hide-scrollbar px-3 pb-3 flex flex-col gap-2 bg-[#fafbfc]">' +
              '<article data-notif-item class="rounded-xl bg-white border border-gray-100 p-3">' +
                '<div class="flex items-start gap-3">' +
                  '<div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-blue-50"><img src="' + logoPath('stickynote-blue-fill.svg') + '" class="size-4" alt="Order"></div>' +
                  '<div class="min-w-0 flex-1">' +
                    '<p class="font-semibold text-[13px] text-custom-black">Pesanan baru #INV-2024-00157</p>' +
                    '<p class="text-xs text-custom-grey mt-1">Segera proses pesanan dari Rina Pratama.</p>' +
                    '<p class="text-[11px] text-custom-grey/80 mt-2">2 menit lalu</p>' +
                  '</div>' +
                  '<button onclick="removeNotification(this, event)" class="flex size-7 items-center justify-center rounded-full hover:bg-red-50 transition-300" aria-label="Hapus notifikasi"><img src="' + logoPath('note-remove-grey.svg') + '" class="size-4" alt="Hapus"></button>' +
                '</div>' +
              '</article>' +
              '<article data-notif-item class="rounded-xl bg-white border border-gray-100 p-3">' +
                '<div class="flex items-start gap-3">' +
                  '<div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-green-50"><img src="' + logoPath('wallet-2-blue-fill.svg') + '" class="size-4" alt="Pembayaran"></div>' +
                  '<div class="min-w-0 flex-1">' +
                    '<p class="font-semibold text-[13px] text-custom-black">Pembayaran berhasil diterima</p>' +
                    '<p class="text-xs text-custom-grey mt-1">Dana Rp 1.750.000 dari #INV-2024-00155 sudah masuk.</p>' +
                    '<p class="text-[11px] text-custom-grey/80 mt-2">15 menit lalu</p>' +
                  '</div>' +
                  '<button onclick="removeNotification(this, event)" class="flex size-7 items-center justify-center rounded-full hover:bg-red-50 transition-300" aria-label="Hapus notifikasi"><img src="' + logoPath('note-remove-grey.svg') + '" class="size-4" alt="Hapus"></button>' +
                '</div>' +
              '</article>' +
              '<article data-notif-item class="rounded-xl bg-white border border-gray-100 p-3">' +
                '<div class="flex items-start gap-3">' +
                  '<div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-indigo-50"><img src="' + logoPath('car-delivery-black.svg') + '" class="size-4" alt="Pengiriman"></div>' +
                  '<div class="min-w-0 flex-1">' +
                    '<p class="font-semibold text-[13px] text-custom-black">Pesanan siap dikirim</p>' +
                    '<p class="text-xs text-custom-grey mt-1">Jadwalkan pengiriman untuk 3 pesanan hari ini.</p>' +
                    '<p class="text-[11px] text-custom-grey/80 mt-2">1 jam lalu</p>' +
                  '</div>' +
                  '<button onclick="removeNotification(this, event)" class="flex size-7 items-center justify-center rounded-full hover:bg-red-50 transition-300" aria-label="Hapus notifikasi"><img src="' + logoPath('note-remove-grey.svg') + '" class="size-4" alt="Hapus"></button>' +
                '</div>' +
              '</article>' +
              '<article data-notif-item class="rounded-xl bg-white border border-gray-100 p-3">' +
                '<div class="flex items-start gap-3">' +
                  '<div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-amber-50"><img src="' + logoPath('card-send-orange-fill.svg') + '" class="size-4" alt="Saldo"></div>' +
                  '<div class="min-w-0 flex-1">' +
                    '<p class="font-semibold text-[13px] text-custom-black">Saldo toko diperbarui</p>' +
                    '<p class="text-xs text-custom-grey mt-1">Saldo Anda sekarang Rp 12.450.000.</p>' +
                    '<p class="text-[11px] text-custom-grey/80 mt-2">3 jam lalu</p>' +
                  '</div>' +
                  '<button onclick="removeNotification(this, event)" class="flex size-7 items-center justify-center rounded-full hover:bg-red-50 transition-300" aria-label="Hapus notifikasi"><img src="' + logoPath('note-remove-grey.svg') + '" class="size-4" alt="Hapus"></button>' +
                '</div>' +
              '</article>' +
              '<div id="notif-empty" class="hidden rounded-xl bg-white border border-dashed border-gray-200 p-4 text-center">' +
                '<p class="text-sm font-semibold text-custom-black">Tidak ada notifikasi</p>' +
                '<p class="text-xs text-custom-grey mt-1">Semua notifikasi sudah dibersihkan</p>' +
              '</div>' +
            '</div>' +
          '</div>' +
        '</div>' +
        /* Avatar + dropdown trigger */
        '<div class="relative ml-2">' +
          '<button id="avatar-btn" onclick="toggleAvatarDropdown()" class="flex items-center gap-2.5 rounded-full hover:bg-gray-50 p-1 transition-300">' +
            '<div class="relative">' +
              '<img src="' + userAvatar + '" class="size-[42px] rounded-full object-cover ring-2 ring-gray-200" alt="avatar">' +
              '<span class="absolute bottom-0.5 right-0.5 size-2.5 rounded-full bg-green-500 ring-2 ring-white"></span>' +
            '</div>' +
          '</button>' +
          /* Dropdown */
          '<div id="avatar-dropdown" class="hidden absolute right-0 top-full mt-3 w-64 bg-white rounded-xl shadow-xl ring-1 ring-gray-100 py-2 z-50">' +
            '<div class="flex items-center gap-3 px-5 py-4 border-b border-gray-100">' +
              '<img src="' + userAvatar + '" class="size-11 rounded-full object-cover" alt="">' +
              '<div class="flex flex-col">' +
                '<p class="font-semibold text-[15px]">' + userName + '</p>' +
                '<p class="text-sm text-custom-grey">' + roleName + '</p>' +
              '</div>' +
            '</div>' +
            '<div class="py-1">' +
              '<a href="#" class="flex items-center gap-3 px-5 py-3 text-[15px] text-gray-700 hover:bg-gray-50 transition-300">' + svgUser + ' My Profile</a>' +
              '<a href="' + (urls.settings || '#') + '" class="flex items-center gap-3 px-5 py-3 text-[15px] text-gray-700 hover:bg-gray-50 transition-300">' + svgSettings + ' Settings</a>' +
            '</div>' +
            '<div class="border-t border-gray-100 pt-1">' +
              '<a href="' + logoutUrl + '" class="flex items-center gap-3 px-5 py-3 text-[15px] text-gray-700 hover:bg-gray-50 transition-300">' + svgLogout + ' Log Out</a>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>' +
    '</header>' +
    '</div>' +

    /* PAGE CONTENT */
    '<div class="flex flex-col flex-1 p-5 lg:p-8 min-w-0">' +
      /* Mobile page title */
      '<h1 id="page-mobile-title" class="lg:hidden font-bold text-xl text-custom-black capitalize mb-5">' + pageTitle + '</h1>' +
      '<div id="page-skeleton" class="flex flex-col gap-5 animate-pulse">' +
        '<div class="bg-white rounded-2xl p-5 lg:p-6">' +
          '<div class="h-6 w-52 bg-gray-200 rounded-lg mb-4"></div>' +
          '<div class="h-4 w-72 bg-gray-100 rounded-lg"></div>' +
        '</div>' +
        '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">' +
          '<div class="bg-white rounded-2xl h-36"></div>' +
          '<div class="bg-white rounded-2xl h-36"></div>' +
          '<div class="bg-white rounded-2xl h-36"></div>' +
          '<div class="bg-white rounded-2xl h-36"></div>' +
        '</div>' +
        '<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">' +
          '<div class="bg-white rounded-2xl h-80 lg:col-span-2"></div>' +
          '<div class="bg-white rounded-2xl h-80"></div>' +
        '</div>' +
      '</div>' +
      '<main id="page-main-content" class="flex flex-col gap-6 flex-1 opacity-0 pointer-events-none">' + mainContent + '</main>' +
    '</div>' +

  '</div>';

  app.innerHTML = layoutHtml;
  app.classList.add('ready');

  var pageCache = {};
  var softNavigating = false;
  var loadedScriptSources = {};
  document.querySelectorAll('script[src]').forEach(function (scriptEl) {
    try {
      loadedScriptSources[new URL(scriptEl.src, window.location.origin).href] = true;
    } catch (e) {
      loadedScriptSources[scriptEl.src] = true;
    }
  });

  function splitMeta(value) {
    if (!value) return [];
    return value.split('||').filter(Boolean);
  }

  function isLinkActive(link) {
    if (!link) return false;
    var href = link.getAttribute('href');
    if (href && href !== '#') {
      if (normalizePath(extractPath(href)) === normalizePath(activePath)) return true;
    }

    var relatedPaths = splitMeta(link.getAttribute('data-related-paths'));
    if (relatedPaths.some(function (path) { return normalizePath(path) === normalizePath(activePath); })) return true;

    var relatedPages = splitMeta(link.getAttribute('data-related-pages'));
    if (relatedPages.indexOf(activePageSlug) !== -1) return true;

    var activePages = splitMeta(link.getAttribute('data-active-pages'));
    if (activePages.indexOf(activePageTitle) !== -1) return true;

    return false;
  }

  function refreshSidebarActiveState() {
    var links = document.querySelectorAll('#sidebar a.sidebar-item[data-sidebar-link="1"]');
    links.forEach(function (link) {
      link.classList.toggle('active', isLinkActive(link));
    });

    var accordionButtons = document.querySelectorAll('#sidebar button[data-accordion-id]');
    accordionButtons.forEach(function (btn) {
      var id = btn.getAttribute('data-accordion-id');
      if (!id) return;
      var container = document.getElementById(id);
      var arrow = document.getElementById(id + '-arrow');
      if (!container) return;

      var hasActive = container.querySelector('a.sidebar-item.active');
      if (hasActive) {
        container.classList.remove('hidden');
        if (arrow) arrow.classList.add('rotate-90');
      } else {
        container.classList.add('hidden');
        if (arrow) arrow.classList.remove('rotate-90');
      }
    });
  }

  function updatePageHeading(title) {
    var safeTitle = title || 'Dashboard';
    var navTitle = document.getElementById('navbar-current-page');
    var mobileTitle = document.getElementById('page-mobile-title');
    if (navTitle) navTitle.textContent = safeTitle;
    if (mobileTitle) mobileTitle.textContent = safeTitle;
  }

  function setMainLoading(isLoading) {
    var main = document.getElementById('page-main-content');
    if (!main) return;
    if (isLoading) {
      main.classList.add('opacity-70', 'pointer-events-none');
    } else {
      main.classList.remove('opacity-70', 'pointer-events-none');
    }
  }

  function showPageSkeleton() {
    var skeleton = document.getElementById('page-skeleton');
    var content = document.getElementById('page-main-content');
    if (skeleton) skeleton.classList.remove('hidden');
    if (content) content.classList.add('opacity-0', 'pointer-events-none');
  }

  function hidePageSkeleton() {
    var skeleton = document.getElementById('page-skeleton');
    var content = document.getElementById('page-main-content');
    if (skeleton) skeleton.classList.add('hidden');
    if (content) content.classList.remove('opacity-0', 'pointer-events-none');
  }

  function waitMinSkeletonDelay(startedAt, minDelayMs) {
    var elapsed = Date.now() - startedAt;
    var remaining = Math.max(0, minDelayMs - elapsed);
    return new Promise(function (resolve) {
      setTimeout(resolve, remaining);
    });
  }

  function collectScripts(doc) {
    var scripts = [];
    doc.querySelectorAll('script').forEach(function (scriptEl) {
      var src = scriptEl.getAttribute('src');
      if (src) {
        if (src.indexOf('admin-layout.js') !== -1) return;
        try {
          scripts.push({ external: true, src: new URL(src, window.location.origin).href });
        } catch (e) {
          scripts.push({ external: true, src: src });
        }
        return;
      }

      var code = scriptEl.textContent || '';
      if (!code.trim()) return;
      if (code.indexOf('__DASHBOARD_CONFIG__') !== -1) return;
      scripts.push({ external: false, code: code });
    });
    return scripts;
  }

  function collectStyles(doc) {
    var styles = { links: [], inline: [] };

    doc.querySelectorAll('link[rel="stylesheet"]').forEach(function (linkEl) {
      var href = linkEl.getAttribute('href');
      if (!href) return;
      // main.css is already globally loaded in every page; no need to re-inject.
      if (href.indexOf('dashboard/assets/css/main.css') !== -1) return;
      try {
        styles.links.push(new URL(href, window.location.origin).href);
      } catch (e) {
        styles.links.push(href);
      }
    });

    doc.querySelectorAll('style').forEach(function (styleEl) {
      var cssText = styleEl.textContent || '';
      if (!cssText.trim()) return;
      styles.inline.push(cssText);
    });

    return styles;
  }

  function applyStyles(stylePayload) {
    if (!stylePayload) return;

    document.querySelectorAll('link[data-soft-page-link="1"]').forEach(function (el) {
      el.parentNode.removeChild(el);
    });
    document.querySelectorAll('style[data-soft-page-style="1"]').forEach(function (el) {
      el.parentNode.removeChild(el);
    });

    (stylePayload.links || []).forEach(function (href) {
      var exists = Array.prototype.some.call(
        document.querySelectorAll('link[rel="stylesheet"]'),
        function (el) {
          try {
            return new URL(el.href, window.location.origin).href === href;
          } catch (e) {
            return el.getAttribute('href') === href;
          }
        }
      );
      if (exists) return;

      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.setAttribute('data-soft-page-link', '1');
      document.head.appendChild(link);
    });

    (stylePayload.inline || []).forEach(function (cssText) {
      var style = document.createElement('style');
      style.setAttribute('data-soft-page-style', '1');
      style.textContent = cssText;
      document.head.appendChild(style);
    });
  }

  function loadExternalScript(src) {
    if (!src || loadedScriptSources[src]) return Promise.resolve();

    return new Promise(function (resolve) {
      var script = document.createElement('script');
      script.src = src;
      script.onload = function () {
        loadedScriptSources[src] = true;
        resolve();
      };
      script.onerror = function () {
        resolve();
      };
      document.body.appendChild(script);
    });
  }

  function runInlineScript(code) {
    if (!code || !code.trim()) return;
    var script = document.createElement('script');
    // Run inline page scripts in isolated scope to avoid repeated top-level const/let collisions
    // when the same page script is executed again through soft-navigation.
    script.text = '(function(){\n' + code + '\n})();';
    document.body.appendChild(script);
    document.body.removeChild(script);
  }

  function runScriptsSequentially(scripts) {
    var chain = Promise.resolve();
    scripts.forEach(function (entry) {
      chain = chain.then(function () {
        if (entry.external) return loadExternalScript(entry.src);
        runInlineScript(entry.code);
        return Promise.resolve();
      });
    });
    return chain;
  }

  function fetchPagePayload(url) {
    var pathKey = normalizePath(extractPath(url));
    if (pageCache[pathKey]) return Promise.resolve(pageCache[pathKey]);

    return fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(function (response) {
        if (!response.ok) throw new Error('Failed to fetch page');
        return response.text();
      })
      .then(function (html) {
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');
        var nextApp = doc.getElementById('admin-app');
        if (!nextApp) throw new Error('Invalid page payload');

        var payload = {
          path: pathKey,
          documentTitle: doc.title || document.title,
          pageTitle: nextApp.getAttribute('data-page-title') || 'Dashboard',
          content: nextApp.innerHTML,
          styles: collectStyles(doc),
          scripts: collectScripts(doc)
        };

        pageCache[pathKey] = payload;
        return payload;
      });
  }

  function isSoftNavigable(url, linkEl) {
    if (!url || !linkEl) return false;
    if (linkEl.hasAttribute('download')) return false;
    if (linkEl.getAttribute('target') === '_blank') return false;
    if (url === '#') return false;
    if (url.indexOf('javascript:') === 0) return false;
    if (url.indexOf('/auth/logout/') !== -1) return false;

    try {
      var targetUrl = new URL(url, window.location.origin);
      if (targetUrl.origin !== window.location.origin) return false;
      return true;
    } catch (e) {
      return false;
    }
  }

  function softNavigate(url, pushToHistory) {
    if (softNavigating) return;

    var targetUrl;
    try {
      targetUrl = new URL(url, window.location.origin);
    } catch (e) {
      targetUrl = new URL(window.location.origin + url);
    }
    var historyPath = targetUrl.pathname + (targetUrl.search || '') + (targetUrl.hash || '');
    var targetPath = normalizePath(extractPath(url));
    if (targetPath === normalizePath(activePath)) return;

    softNavigating = true;
    var navStartTime = Date.now();
    var minSkeletonDelayMs = 320;
    showPageSkeleton();
    setMainLoading(true);

    fetchPagePayload(url)
      .then(function (payload) {
        var contentEl = document.getElementById('page-main-content');
        if (!contentEl) throw new Error('Main content container not found');

        contentEl.innerHTML = payload.content;
        applyStyles(payload.styles);

        activePath = payload.path;
        activePageSlug = (payload.path.split('/').filter(Boolean).pop() || 'index').toLowerCase();
        activePageTitle = payload.pageTitle || 'Dashboard';

        document.title = payload.documentTitle;
        updatePageHeading(activePageTitle);
        refreshSidebarActiveState();
        closeSidebar();

        if (pushToHistory) {
          window.history.pushState({ path: payload.path }, '', historyPath);
        }

        // Ensure toast library is ready on every page transition,
        // even when there are no Django flash messages.
        ensureSweetAlertReady();

        return runScriptsSequentially(payload.scripts).then(function () {
          return waitMinSkeletonDelay(navStartTime, minSkeletonDelayMs).then(function () {
            hidePageSkeleton();
          });
        }).then(function () {
          showDjangoToastsFromWindow();
        });
      })
      .catch(function () {
        window.location.href = url;
      })
      .finally(function () {
        softNavigating = false;
        setMainLoading(false);
      });
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;

    // Limit soft-navigation to sidebar and top-navbar navigations to keep behavior predictable.
    if (!link.closest('#sidebar') && !link.closest('#top-navbar')) return;

    var href = link.getAttribute('href');
    if (!isSoftNavigable(href, link)) return;

    e.preventDefault();
    softNavigate(href, true);
  });

  document.addEventListener('mouseover', function (e) {
    var link = e.target.closest('#sidebar a.sidebar-item[href]');
    if (!link) return;
    if (link.dataset.prefetched === '1') return;

    var href = link.getAttribute('href');
    if (!isSoftNavigable(href, link)) return;

    link.dataset.prefetched = '1';
    fetchPagePayload(href).catch(function () {});
  });

  window.addEventListener('popstate', function () {
    softNavigate(window.location.href, false);
  });

  function revealPageContent() {
    hidePageSkeleton();
  }

  // Reveal after full page load, with fallback to avoid skeleton getting stuck.
  if (document.readyState === 'complete') {
    setTimeout(revealPageContent, 120);
  } else {
    window.addEventListener('load', function () {
      setTimeout(revealPageContent, 120);
    }, { once: true });
    setTimeout(revealPageContent, 1800);
  }

  // Always preload local SweetAlert2 so page-level actions (e.g. Reset toast)
  // can show notifications even when there are no Django messages.
  ensureSweetAlertReady();
  setTimeout(showDjangoToastsFromWindow, 60);

  /* ── Close dropdown on outside click ──────────────────────── */
  document.addEventListener('click', function (e) {
    var dd = document.getElementById('avatar-dropdown');
    var btn = document.getElementById('avatar-btn');
    if (dd && btn && !btn.contains(e.target) && !dd.contains(e.target)) {
      dd.classList.add('hidden');
    }

    var notifDd = document.getElementById('notif-dropdown');
    var notifBtn = document.getElementById('notif-btn');
    if (notifDd && notifBtn && !notifBtn.contains(e.target) && !notifDd.contains(e.target)) {
      notifDd.classList.add('hidden');
    }
  });
});

/* ── Global functions ─────────────────────────────────────────── */
function toggleAccordion(id) {
  var el = document.getElementById(id);
  var arrow = document.getElementById(id + '-arrow');
  if (!el) return;
  if (el.classList.contains('hidden')) {
    el.classList.remove('hidden');
    if (arrow) arrow.classList.add('rotate-90');
  } else {
    el.classList.add('hidden');
    if (arrow) arrow.classList.remove('rotate-90');
  }
}

function openSidebar() {
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.remove('-translate-x-full');
  if (overlay) overlay.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.add('-translate-x-full');
  if (overlay) overlay.classList.add('hidden');
  document.body.style.overflow = '';
}

function toggleSidebarCollapse() {
  var sidebar = document.getElementById('sidebar');
  var mainWrapper = document.getElementById('main-wrapper');
  if (!sidebar || !mainWrapper) return;
  if (sidebar.classList.contains('-translate-x-full')) {
    sidebar.classList.remove('-translate-x-full');
    mainWrapper.classList.remove('lg:ml-0');
    mainWrapper.classList.add('lg:ml-[280px]');
  } else {
    sidebar.classList.add('-translate-x-full');
    mainWrapper.classList.remove('lg:ml-[280px]');
    mainWrapper.classList.add('lg:ml-0');
  }
}

function toggleAvatarDropdown() {
  var dd = document.getElementById('avatar-dropdown');
  if (dd) dd.classList.toggle('hidden');
}

function updateNotificationState() {
  var items = document.querySelectorAll('[data-notif-item]');
  var count = items.length;
  var badge = document.getElementById('notif-badge');
  var emptyState = document.getElementById('notif-empty');
  var countText = document.getElementById('notif-count');

  if (badge) badge.classList.toggle('hidden', count === 0);
  if (emptyState) emptyState.classList.toggle('hidden', count !== 0);
  if (countText) countText.textContent = count + ' notifikasi terbaru';
}

function toggleNotificationDropdown(event) {
  if (event) event.stopPropagation();
  var dd = document.getElementById('notif-dropdown');
  if (!dd) return;
  dd.classList.toggle('hidden');
  updateNotificationState();
}

function removeNotification(button, event) {
  if (event) event.stopPropagation();
  var item = button ? button.closest('[data-notif-item]') : null;
  if (!item) return;
  item.remove();
  updateNotificationState();
}

function clearNotifications(event) {
  if (event) event.stopPropagation();
  document.querySelectorAll('[data-notif-item]').forEach(function (item) {
    item.remove();
  });
  updateNotificationState();
}
