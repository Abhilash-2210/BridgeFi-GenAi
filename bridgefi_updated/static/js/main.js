/**
 * BridgeFi V3 — Main JavaScript
 * Theme toggle, auth system, modal management, toast notifications
 */

// ================================================================
// THEME SYSTEM
// ================================================================
function initTheme() {
  const saved = localStorage.getItem('bridgefi-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('bridgefi-theme', next);
}

// Run immediately to avoid flash
initTheme();

// ================================================================
// AUTH STATE (localStorage-based simulation)
// ================================================================
const AUTH_KEY = 'bridgefi_user';

function getUser() {
  try { return JSON.parse(localStorage.getItem(AUTH_KEY)); } catch { return null; }
}

function setUser(user) {
  localStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

function clearUser() {
  localStorage.removeItem(AUTH_KEY);
}

function updateNavAuth() {
  const user = getUser();
  const authArea  = document.getElementById('navAuthArea');
  const userArea  = document.getElementById('navUserArea');
  if (!authArea || !userArea) return;

  if (user) {
    authArea.classList.add('hidden');
    userArea.classList.remove('hidden');
    const initial = (user.name || user.email || 'U')[0].toUpperCase();
    ['userAvatarInitial','udAvatar'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = initial;
    });
    const nameEl = document.getElementById('userNameNav');
    const udNameEl = document.getElementById('udName');
    const udEmailEl = document.getElementById('udEmail');
    if (nameEl) nameEl.textContent = user.name ? user.name.split(' ')[0] : 'User';
    if (udNameEl) udNameEl.textContent = user.name || 'User';
    if (udEmailEl) udEmailEl.textContent = user.email || '';
  } else {
    authArea.classList.remove('hidden');
    userArea.classList.add('hidden');
  }
}

function toggleUserMenu() {
  const dd = document.getElementById('userDropdown');
  if (dd) dd.classList.toggle('hidden');
}

// Close dropdown on outside click
document.addEventListener('click', e => {
  const nav = document.querySelector('.nav-user');
  const dd  = document.getElementById('userDropdown');
  if (dd && nav && !nav.contains(e.target)) dd.classList.add('hidden');
});

function submitLogin() {
  const email    = document.getElementById('login-email')?.value.trim();
  const password = document.getElementById('login-password')?.value;
  const btn      = document.getElementById('loginSubmitBtn');

  if (!email || !password) { showToast('Please fill all fields', 'error'); return; }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showToast('Enter a valid email', 'error'); return; }
  if (password.length < 6) { showToast('Password too short', 'error'); return; }

  // Simulate async login
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';
  btn.disabled = true;

  setTimeout(() => {
    const stored = JSON.parse(localStorage.getItem('bridgefi_users') || '{}');
    const userRecord = stored[email];

    if (!userRecord) {
      showToast('No account found. Please sign up.', 'error');
      btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
      btn.disabled = false;
      return;
    }
    if (userRecord.password !== btoa(password)) {
      showToast('Incorrect password', 'error');
      btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
      btn.disabled = false;
      return;
    }

    setUser({ name: userRecord.name, email: email, role: userRecord.role });
    closeModal('loginModal');
    updateNavAuth();
    showToast('Welcome back, ' + (userRecord.name ? userRecord.name.split(' ')[0] : 'User') + '! 👋');
    btn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Sign In';
    btn.disabled = false;
  }, 900);
}

function submitSignup() {
  const name     = document.getElementById('signup-name')?.value.trim();
  const email    = document.getElementById('signup-email')?.value.trim();
  const password = document.getElementById('signup-password')?.value;
  const role     = document.querySelector('input[name="role"]:checked')?.value || 'applicant';
  const btn      = document.getElementById('signupSubmitBtn');

  if (!name || !email || !password) { showToast('Please fill all fields', 'error'); return; }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showToast('Enter a valid email', 'error'); return; }
  if (password.length < 8) { showToast('Password must be at least 8 characters', 'error'); return; }

  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating account...';
  btn.disabled = true;

  setTimeout(() => {
    const stored = JSON.parse(localStorage.getItem('bridgefi_users') || '{}');
    if (stored[email]) {
      showToast('Email already registered. Please login.', 'error');
      btn.innerHTML = '<i class="fas fa-rocket"></i> Create Free Account';
      btn.disabled = false;
      return;
    }
    stored[email] = { name, password: btoa(password), role };
    localStorage.setItem('bridgefi_users', JSON.stringify(stored));

    setUser({ name, email, role });
    closeModal('signupModal');
    updateNavAuth();
    showToast('Account created! Welcome to BridgeFi 🎉');
    btn.innerHTML = '<i class="fas fa-rocket"></i> Create Free Account';
    btn.disabled = false;
  }, 1000);
}

function submitForgot() {
  const email = document.getElementById('forgot-email')?.value.trim();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    showToast('Enter a valid email address', 'error'); return;
  }
  const el = document.getElementById('resetEmailDisplay');
  if (el) el.textContent = email;
  closeModal('forgotModal');
  openModal('resetSuccessModal');
}

function switchToForgot() {
  const loginEmail = document.getElementById('login-email')?.value;
  closeModal('loginModal');
  openModal('forgotModal');
  const forgotEmail = document.getElementById('forgot-email');
  if (forgotEmail && loginEmail) forgotEmail.value = loginEmail;
}

function logoutUser() {
  clearUser();
  updateNavAuth();
  const dd = document.getElementById('userDropdown');
  if (dd) dd.classList.add('hidden');
  showToast('Signed out. See you soon!');
}

function socialLogin(provider) {
  const name  = provider === 'google' ? 'Demo User' : 'Dev User';
  const email = provider === 'google' ? 'demo@gmail.com' : 'dev@github.com';
  setUser({ name, email, role: 'applicant' });
  ['loginModal','signupModal'].forEach(id => closeModal(id));
  updateNavAuth();
  showToast('Signed in with ' + provider.charAt(0).toUpperCase() + provider.slice(1) + ' ✓');
}

function switchModal(from, to) {
  closeModal(from);
  setTimeout(() => openModal(to), 150);
}

// Password strength meter
document.addEventListener('input', e => {
  if (e.target.id !== 'signup-password') return;
  const val = e.target.value;
  const bar = document.getElementById('psBar');
  const label = document.getElementById('psLabel');
  if (!bar) return;
  let score = 0;
  if (val.length >= 8) score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  const pct  = [0, 25, 50, 75, 100][score];
  const cols = ['', '#ef4444', '#f59e0b', '#6366f1', '#10b981'][score];
  const labs = ['', 'Weak', 'Fair', 'Good', 'Strong'][score];
  bar.style.width = pct + '%';
  bar.style.background = cols;
  if (label) { label.textContent = labs; label.style.color = cols; }
});

// Toggle password visibility
function togglePwd(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.innerHTML = '<i class="fas fa-eye-slash"></i>';
  } else {
    input.type = 'password';
    btn.innerHTML = '<i class="fas fa-eye"></i>';
  }
}

// ================================================================
// MODALS
// ================================================================
function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add('hidden');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal:not(.hidden)').forEach(m => m.classList.add('hidden'));
    document.body.style.overflow = '';
  }
});

// ================================================================
// TOAST
// ================================================================
let toastTimer = null;

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  const msg  = document.getElementById('toast-msg');
  const icon = toast.querySelector('.toast-icon i');
  if (msg) msg.textContent = message;
  if (icon) icon.className = type === 'error' ? 'fas fa-exclamation-circle' : 'fas fa-check-circle';
  toast.className = 'toast' + (type === 'error' ? ' error' : '');
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.add('hidden'), 3200);
}

// ================================================================
// DOMContentLoaded
// ================================================================
document.addEventListener('DOMContentLoaded', () => {
  updateNavAuth();

  // Date inputs default to today
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach(input => {
    if (!input.value) input.value = today;
  });
});
