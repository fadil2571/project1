// ── NAVIGATION ──
function go(el, id) {
  document.querySelectorAll('.pg').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));
  const pg = document.getElementById('pg-' + id);
  if (pg) {
    pg.classList.add('active');
    pg.closest('.content').scrollTop = 0;
  }
  else {
    const routes = {
      home: '/',
      kategori: '/kategori/',
      product: '/product/',
      cart: '/cart/',
      checkout: '/checkout/',
      payment: '/payment/',
      orders: '/orders/',
      order_tracking: '/orders/',
      wishlist: '/wishlist/',
      notif: '/notif/',
      wallet: '/wallet/',
      profile: '/profile/',
      login: '/login/',
      register: '/register/',
      landing: '/'
    };
    if (routes[id]) {
      window.location.href = routes[id];
      return;
    }
  }
  if (el) el.classList.add('active');
  else {
    document.querySelectorAll('.mobile-nav-btn').forEach(b => {
      if (b.getAttribute('onclick') && b.getAttribute('onclick').includes("'" + id + "'"))
        b.classList.add('active');
    });
  }
  // Haptic feedback on mobile
  if (navigator.vibrate) navigator.vibrate(10);
}



// ── TOAST ──
function toast(msg, type = 'success') {
  const w = document.getElementById('tw');
  const t = document.createElement('div');
  t.className = 'toast ' + type;
  const ico = { success: '✅', error: '❌', info: 'ℹ️' };
  t.innerHTML = `<span>${ico[type] || 'ℹ️'}</span><span>${msg}</span>`;
  w.appendChild(t);
  setTimeout(() => {
    t.style.cssText = 'opacity:0;transform:translateX(60px);transition:all .3s';
    setTimeout(() => t.remove(), 300);
  }, 3000);
}

// ── QUANTITY CONTROL ──
let q = 1;
function adjQ(d) {
  q = Math.max(1, q + d);
  document.getElementById('qmain').value = q;
}
function adjCQ(d, id) {
  const el = document.getElementById(id);
  el.value = Math.max(1, parseInt(el.value) + d);
}

// ── VARIANT SELECTION ──
function selVar(btn) {
  btn.closest('.varopts').querySelectorAll('.varbtn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

// ── GALLERY ──
function setGal(el, e) {
  document.querySelectorAll('.gth').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('galMain').textContent = e;
}

// ── PAYMENT SELECTION ──
function selPay(el) {
  el.closest('.card,.co-sec,#pg-payment').querySelectorAll('.pay-mth').forEach(m => {
    m.classList.remove('sel');
    const rd = m.querySelector('.rd');
    if (rd) rd.remove();
  });
  el.classList.add('sel');
  const rw = el.querySelector('.rw');
  if (rw && !rw.querySelector('.rd')) {
    const rd = document.createElement('div');
    rd.className = 'rd';
    rw.appendChild(rd);
  }
}

// ── PASSWORD TOGGLE ──
function eye(id) {
  const el = document.getElementById(id);
  el.type = el.type === 'password' ? 'text' : 'password';
}

// ── REGISTER ROLE TOGGLE ──
function setRegisterRole(role, button) {
  const card = document.querySelector('.register-card');
  if (!card) return;

  card.dataset.registerRole = role;

  const roleInput = document.getElementById('registerAccountType');
  if (roleInput) roleInput.value = role;

  const buttons = card.querySelectorAll('.register-role-btn');
  buttons.forEach(btn => {
    const isActive = btn === button;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });

  syncRegisterFieldState(role, card);
}

function syncRegisterFieldState(role, card) {
  const buyerFields = card.querySelectorAll('.register-form-buyer input, .register-form-buyer select, .register-form-buyer textarea');
  const sellerFields = card.querySelectorAll('.register-form-seller input, .register-form-seller select, .register-form-seller textarea');

  const isBuyer = role === 'buyer';

  buyerFields.forEach(field => {
    field.disabled = !isBuyer;
    if (!isBuyer) {
      field.dataset.wasRequired = field.required ? '1' : '0';
      field.required = false;
      return;
    }
    if (field.dataset.wasRequired === '1') {
      field.required = true;
    }
  });

  sellerFields.forEach(field => {
    field.disabled = isBuyer;
    if (isBuyer) {
      field.dataset.wasRequired = field.required ? '1' : '0';
      field.required = false;
      return;
    }
    if (field.dataset.wasRequired === '1') {
      field.required = true;
    }
  });
}

// ── AUTH ──
function doLogin() {
  const e = document.getElementById('lemail');
  if (!e || !e.value) {
    toast('Masukkan email terlebih dahulu', 'error');
    return;
  }
  toast('Login berhasil! Selamat datang kembali 👋', 'success');
  setTimeout(() => go(null, 'home'), 900);
}

function doReg() {
  const e = document.getElementById('remail'),
    p = document.getElementById('rpass'),
    p2 = document.getElementById('rpass2');
  if (!e || !e.value) {
    toast('Email tidak boleh kosong', 'error');
    return;
  }
  if (!p || p.value.length < 8) {
    toast('Password minimal 8 karakter', 'error');
    return;
  }
  if (p.value !== p2.value) {
    toast('Konfirmasi password tidak cocok', 'error');
    return;
  }
  toast('Akun berhasil dibuat! Selamat datang 🎉', 'success');
  setTimeout(() => go(null, 'home'), 900);
}

function doPay() {
  toast('Memproses pembayaran via Midtrans...', 'info');
  setTimeout(() => {
    toast('Pembayaran berhasil! 🎉', 'success');
    setTimeout(() => go(null, 'success'), 600);
  }, 1800);
}

// ── CHAT ──
function sendChat() {
  const inp = document.getElementById('chatIn');
  if (!inp.value.trim()) return;
  const msgs = inp.closest('.chat-main').querySelector('.chat-msgs');
  const d = document.createElement('div');
  d.className = 'msg mine';
  d.innerHTML = `<div class="msg-ava">BS</div><div><div class="msg-bubble">${inp.value}</div><div class="msg-time">Sekarang</div></div>`;
  msgs.appendChild(d);
  msgs.scrollTop = msgs.scrollHeight;
  inp.value = '';
  setTimeout(() => {
    const r = document.createElement('div');
    r.className = 'msg';
    r.innerHTML = `<div class="msg-ava">🍎</div><div><div class="msg-bubble">Terima kasih kak! Ada yang bisa kami bantu lagi? 😊</div><div class="msg-time">Sekarang</div></div>`;
    msgs.appendChild(r);
    msgs.scrollTop = msgs.scrollHeight;
  }, 1200);
}

// ── COUNTDOWN TIMER ──
let secs = 2 * 3600 + 47 * 60 + 13;
setInterval(() => {
  const h = String(Math.floor(secs / 3600)).padStart(2, '0');
  const m = String(Math.floor((secs % 3600) / 60)).padStart(2, '0');
  const s = String(secs % 60).padStart(2, '0');
  const ch = document.getElementById('ch'),
    cm = document.getElementById('cm'),
    cs = document.getElementById('cs');
  if (ch) ch.textContent = h;
  if (cm) cm.textContent = m;
  if (cs) cs.textContent = s;
  if (secs > 0) secs--;
}, 1000);




/* ════════════════════════════════════════════════════════ */
/* ──────────── MOBILE TOUCH & SWIPE FEATURES ──────────── */
/* ════════════════════════════════════════════════════════ */

// ── TOUCH SWIPE GESTURE ──
let touchStartX = 0;
let touchEndX = 0;
function handleSwipe() {
  const diff = touchEndX - touchStartX;
  // Gallery swipe
  const galThumbs = document.querySelectorAll('.gth');
  if (galThumbs.length > 0) {
    const activeThumbnail = document.querySelector('.gth.active');
    let activeIndex = Array.from(galThumbs).indexOf(activeThumbnail);
    if (diff > 50 && activeIndex > 0) {
      // Swipe right - previous
      galThumbs[activeIndex - 1].click();
      if (navigator.vibrate) navigator.vibrate(10);
    } else if (diff < -50 && activeIndex < galThumbs.length - 1) {
      // Swipe left - next
      galThumbs[activeIndex + 1].click();
      if (navigator.vibrate) navigator.vibrate(10);
    }
  }
}

// Add touch listeners for swipe
document.addEventListener('touchstart', (e) => {
  touchStartX = e.changedTouches[0].screenX;
}, false);

document.addEventListener('touchend', (e) => {
  touchEndX = e.changedTouches[0].screenX;
  handleSwipe();
}, false);

// ── KEYBOARD DETECTION ON MOBILE ──
let isKeyboardOpen = false;
window.addEventListener('resize', () => {
  const currentHeight = window.innerHeight;
  const originalHeight = screen.height;
  isKeyboardOpen = currentHeight < originalHeight * 0.85;
});

// ── DOUBLE TAP TO ZOOM (PRODUCT ITEMS) ──
let lastTapTime = 0;
document.addEventListener('touchend', (e) => {
  const currentTime = new Date().getTime();
  const tapLength = currentTime - lastTapTime;
  if (tapLength < 300 && tapLength > 0) {
    const target = e.target.closest('.pc,.card');
    if (target) {
      target.style.transform = 'scale(1.05)';
      setTimeout(() => {
        target.style.transform = 'scale(1)';
        if (navigator.vibrate) navigator.vibrate(20);
      }, 200);
    }
  }
  lastTapTime = currentTime;
});

// ── PREVENT DOUBLE ZOOM ON INPUT ──
document.addEventListener('touchmove', (e) => {
  if (e.target.matches('input, textarea')) {
    e.stopPropagation();
  }
}, { passive: false });

// ── SMOOTH SCROLL BEHAVIOR ──
document.querySelectorAll('a[onclick*="go"]').forEach(el => {
  el.addEventListener('click', (e) => {
    setTimeout(() => {
      const content = document.querySelector('.content');
      if (content) content.scrollTop = 0;
    }, 50);
  });
});

// ── MOBILE FORM INPUT ENHANCEMENTS ──
document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"], textarea').forEach(input => {
  // Auto-focus management
  input.addEventListener('focus', () => {
    if (isKeyboardOpen && input.offsetTop > window.innerHeight * 0.5) {
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  });
  
  // Touch visual feedback
  input.addEventListener('touchstart', () => {
    input.style.background = 'var(--white)';
  });
});

// ── BUTTON TAP FEEDBACK ──
document.querySelectorAll('.btn, .icobtn, .ni, .mobile-nav-btn').forEach(btn => {
  btn.addEventListener('touchstart', function() {
    this.style.opacity = '0.7';
    if (navigator.vibrate) navigator.vibrate([5, 20, 5]);
  });
  
  btn.addEventListener('touchend', function() {
    this.style.opacity = '1';
  });
  
  btn.addEventListener('touchcancel', function() {
    this.style.opacity = '1';
  });
});



// ── ORIENTATION CHANGE HANDLING ──
window.addEventListener('orientationchange', () => {
  // Re-adjust view
  setTimeout(() => {
    document.querySelector('.content').scrollTop = 0;
  }, 300);
});

// ── LONG PRESS DETECTION (FOR FAVORITES) ──
let longPressTimer = null;
let longPressDetails = {};

document.addEventListener('touchstart', (e) => {
  const target = e.target.closest('.pc, .ni');
  if (target) {
    longPressDetails = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    longPressTimer = setTimeout(() => {
      if (navigator.vibrate) navigator.vibrate([20, 10, 20]);
      // Could trigger context menu or favorite toggle here
      console.log('Long press detected');
    }, 500);
  }
});

document.addEventListener('touchend', () => {
  clearTimeout(longPressTimer);
});

document.addEventListener('touchmove', (e) => {
  if (longPressTimer) {
    const touch = e.touches[0];
    const distance = Math.sqrt(
      Math.pow(touch.clientX - longPressDetails.x, 2) +
      Math.pow(touch.clientY - longPressDetails.y, 2)
    );
    if (distance > 20) {
      clearTimeout(longPressTimer);
    }
  }
}, { passive: true });

// ── HERO CAROUSEL ──
let heroIdx = -1;
let heroTimer = null;
function heroGoTo(idx) {
  const slides = document.querySelectorAll('.lp-hero-slide');
  const dots = document.querySelectorAll('.lp-hero-dots .lp-dot');
  const dotsWrap = document.querySelector('.lp-hero-dots');
  if (!slides.length) return;
  slides.forEach(s => { s.classList.remove('active'); s.classList.remove('leaving'); });
  dots.forEach(d => d.classList.remove('active'));
  const prev = slides[heroIdx];
  if (prev && heroIdx !== (idx % slides.length)) prev.classList.add('leaving');
  heroIdx = idx % slides.length;
  slides[heroIdx].classList.add('active');
  if (dots[heroIdx]) dots[heroIdx].classList.add('active');
  // Adjust dot colors for light slides
  if (dotsWrap) {
    dotsWrap.classList.toggle('lp-dots-dark', heroIdx === 1);
  }
  // Reset timer
  clearInterval(heroTimer);
  heroTimer = setInterval(heroNext, 3000);
}
function heroNext() { heroGoTo(heroIdx + 1); }
function heroStartAuto() {
  heroTimer = setInterval(heroNext, 3000);
}

// ── REKOMENDASI CAROUSEL ──
let rekomendasiIdx = 0;
let rekomendasiTimer = null;
const rekomendasiIntervalMs = 3000;

function rekomendasiRestartTimer() {
  clearInterval(rekomendasiTimer);
  rekomendasiTimer = setInterval(rekomendasiNext, rekomendasiIntervalMs);
}

function rekomendasiGoTo(idx) {
  const slides = Array.from(document.querySelectorAll('.rekomendasi-slide'));
  const dots = document.querySelectorAll('.rekomendasi-dot');
  if (!slides.length) return;

  const nextIdx = (idx + slides.length) % slides.length;

  if (nextIdx === rekomendasiIdx) {
    slides.forEach((s, i) => {
      s.classList.remove('leaving');
      s.classList.toggle('active', i === rekomendasiIdx);
    });
    dots.forEach((d, i) => d.classList.toggle('active', i === rekomendasiIdx));
    rekomendasiRestartTimer();
    return;
  }

  slides.forEach(s => {
    s.classList.remove('active');
    s.classList.remove('leaving');
  });
  dots.forEach(d => d.classList.remove('active'));

  const prev = slides[rekomendasiIdx];
  if (prev) prev.classList.add('leaving');

  rekomendasiIdx = nextIdx;
  slides[rekomendasiIdx].classList.add('active');
  if (dots[rekomendasiIdx]) dots[rekomendasiIdx].classList.add('active');

  rekomendasiRestartTimer();
}
function rekomendasiNext() { rekomendasiGoTo(rekomendasiIdx + 1); }
function rekomendasiStartAuto() {
  const slides = Array.from(document.querySelectorAll('.rekomendasi-slide'));
  if (!slides.length) return;

  const activeIdx = slides.findIndex(slide => slide.classList.contains('active'));
  rekomendasiIdx = activeIdx >= 0 ? activeIdx : 0;
  rekomendasiGoTo(rekomendasiIdx);
}

// ── INITIAL SETUP ──
document.addEventListener('DOMContentLoaded', () => {
  const registerCard = document.querySelector('.register-card');
  if (registerCard) {
    const selectedRole = registerCard.dataset.registerRole || 'buyer';
    syncRegisterFieldState(selectedRole, registerCard);
  }

  // Start hero carousel
  heroGoTo(0);
  rekomendasiStartAuto();

  const rekomendasiSlider = document.getElementById('rekomendasiSlider');
  if (rekomendasiSlider) {
    rekomendasiSlider.addEventListener('mouseenter', () => clearInterval(rekomendasiTimer));
    rekomendasiSlider.addEventListener('mouseleave', () => {
      rekomendasiRestartTimer();
    });
  }

  // Set initial active state for mobile nav
  const activePage = document.querySelector('.pg.active');
  if (activePage) {
    const pageId = activePage.id.replace('pg-', '');
    document.querySelectorAll('.mobile-nav-btn').forEach(btn => {
      if (btn.getAttribute('onclick').includes(`'${pageId}'`)) {
        btn.classList.add('active');
      }
    });
  }

  // ── USER MENU DROPDOWN ──
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userDropdown = document.getElementById('userDropdown');

  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isExpanded = userMenuBtn.getAttribute('aria-expanded') === 'true';
      userMenuBtn.setAttribute('aria-expanded', !isExpanded);
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!userDropdown.contains(e.target) && !userMenuBtn.contains(e.target)) {
        userDropdown.classList.remove('show');
        userMenuBtn.setAttribute('aria-expanded', 'false');
      }
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && userDropdown.classList.contains('show')) {
        userDropdown.classList.remove('show');
        userMenuBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }
});
