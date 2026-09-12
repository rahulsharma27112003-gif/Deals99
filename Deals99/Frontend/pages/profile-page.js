/**
 * Profile page — /api/profile/me/ and /api/orders/ for stats and recent orders.
 */
import {
  fetchUserProfile,
  updateUserProfile,
  fetchOrders,
  fetchWishlist,
  isAuthenticated,
  logoutUser,
  getCurrentUser,
  setCurrentUser,
} from '../api.js';

function formatMoney(n) {
  return `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

class ProfilePageManager {
  constructor() {
    this.userData = {};
    this.init();
  }

  async init() {
    if (!isAuthenticated()) {
      window.location.href = 'login.html?next=profile.html';
      return;
    }
    await this.loadUserData();
    await this.loadStatsAndOrders();
    this.loadPreferences();
    this.setupEventListeners();
  }

  async loadUserData() {
    try {
      this.userData = await fetchUserProfile();
      const currentUser = getCurrentUser() || {};
      setCurrentUser({
        ...currentUser,
        email: this.userData.email,
        first_name: this.userData.first_name,
        last_name: this.userData.last_name,
        username: this.userData.username,
      });
    } catch (e) {
      console.error('profile-page: load failed', e);
      this.userData = getCurrentUser() || {};
    }
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val ?? '';
    };
    setVal('firstName', this.userData.first_name);
    setVal('lastName', this.userData.last_name);
    setVal('email', this.userData.email);
    setVal('phone', this.userData.phone);
    setVal('dateOfBirth', this.userData.date_of_birth || this.userData.birth_date);
    setVal('gender', this.userData.gender);
    setVal('address', this.userData.address);
    this.updateProfileDisplay();
  }

  updateProfileDisplay() {
    const name = `${this.userData.first_name || ''} ${this.userData.last_name || ''}`.trim() || 'User';
    const nameEl = document.getElementById('profileName');
    const emailEl = document.getElementById('profileEmail');
    if (nameEl) nameEl.textContent = name;
    if (emailEl) emailEl.textContent = this.userData.email || '';
  }

  async loadStatsAndOrders() {
    let orders = [];
    let wishlistCount = 0;
    try {
      orders = await fetchOrders();
    } catch (e) {
      console.warn('profile-page: orders', e);
    }
    try {
      const wl = await fetchWishlist();
      wishlistCount = (wl || []).length;
    } catch (e) {
      const key = window.CONFIG?.STORAGE_KEYS?.WISHLIST || 'wishlist';
      wishlistCount = (window.StorageManager?.get(key) || []).length;
    }

    const totalSpent = (orders || []).reduce((s, o) => s + parseFloat(o.total_amount || 0), 0);
    const set = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };
    set('totalOrders', (orders || []).length);
    set('totalSpent', formatMoney(totalSpent));
    set('wishlistItems', wishlistCount);
    set('reviews', '0');

    this.renderRecentOrders((orders || []).slice(0, 5));
  }

  renderRecentOrders(orders) {
    const container = document.getElementById('recentOrders');
    if (!container) return;
    if (!orders.length) {
      container.innerHTML = '<p class="text-muted">No recent orders. <a href="products.html">Shop now</a></p>';
      return;
    }
    container.innerHTML = orders
      .map((order) => {
        const date = new Date(order.created_at).toLocaleDateString('en-IN');
        const first = (order.items || [])[0];
        const label = first?.product_name || `Order #${order.order_number || order.id}`;
        return `
          <div class="order-item d-flex align-items-center gap-3 py-2 border-bottom">
            <div class="flex-grow-1">
              <div class="fw-semibold small">${label}</div>
              <div class="text-muted small">${date} · ${formatMoney(order.total_amount)}</div>
            </div>
            <span class="badge bg-secondary">${(order.status || 'pending').toUpperCase()}</span>
            <a href="order.html?orderId=${order.order_number || order.id}" class="btn btn-sm btn-outline-primary">View</a>
          </div>`;
      })
      .join('');
  }

  setupEventListeners() {
    document.getElementById('personalForm')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.savePersonalInfo();
    });
    document.getElementById('securityForm')?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.updatePassword();
    });
  }

  async savePersonalInfo() {
    const form = document.getElementById('personalForm');
    const data = new FormData(form);
    const payload = {
      first_name: data.get('firstName'),
      last_name: data.get('lastName'),
      email: data.get('email'),
      phone: data.get('phone'),
      date_of_birth: data.get('dateOfBirth') || null,
      gender: data.get('gender') || '',
      address: data.get('address') || '',
      newsletter_subscribed: document.getElementById('newsletterSubscription')?.checked ?? false,
    };
    try {
      await updateUserProfile(payload);
      window.NotificationManager?.show('Profile updated', 'success');
      await this.loadUserData();
    } catch (e) {
      window.NotificationManager?.show(e.message || 'Failed to update profile', 'error');
    }
  }

  updatePassword() {
    const newPassword = document.getElementById('newPassword')?.value;
    const confirmPassword = document.getElementById('confirmPassword')?.value;
    if (newPassword !== confirmPassword) {
      window.NotificationManager?.show('Passwords do not match', 'error');
      return;
    }
    if (!newPassword || newPassword.length < 8) {
      window.NotificationManager?.show('Use at least 8 characters', 'error');
      return;
    }
    window.NotificationManager?.show('Password change API coming soon — use reset flow', 'info');
    document.getElementById('securityForm')?.reset();
  }

  loadPreferences() {
    const prefs = JSON.parse(localStorage.getItem('userPreferences') || '{}');
    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.checked = !!val;
    };
    set('emailNotifications', prefs.emailNotifications !== false);
    set('smsNotifications', prefs.smsNotifications === true);
    set('newsletterSubscription', prefs.newsletterSubscription ?? this.userData.newsletter_subscribed);
    set('twoFactorAuth', prefs.twoFactorAuth === true);
    set('locationServices', prefs.locationServices === true);
  }

  savePreferences() {
    const preferences = {
      emailNotifications: document.getElementById('emailNotifications')?.checked,
      smsNotifications: document.getElementById('smsNotifications')?.checked,
      newsletterSubscription: document.getElementById('newsletterSubscription')?.checked,
      twoFactorAuth: document.getElementById('twoFactorAuth')?.checked,
      locationServices: document.getElementById('locationServices')?.checked,
    };
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
    updateUserProfile({ newsletter_subscribed: preferences.newsletterSubscription }).catch(() => {});
    window.NotificationManager?.show('Preferences saved', 'success');
  }
}

window.showTab = function showTab(tabName, button) {
  document.querySelectorAll('.tab-content').forEach((t) => t.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
  document.getElementById(`${tabName}Tab`)?.classList.add('active');
  const activeButton = button || document.querySelector(`.tab-btn[data-tab="${tabName}"]`) || document.querySelector(`.btn-profile[data-tab="${tabName}"]`);
  activeButton?.classList?.add('active');
};

window.updateAvatar = function updateAvatar(input) {
  if (input.files?.[0]) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = document.getElementById('profileAvatar');
      if (img) img.src = e.target.result;
    };
    reader.readAsDataURL(input.files[0]);
  }
};

window.savePreferences = function savePreferences() {
  window.profilePageManager?.savePreferences();
};

window.logout = function logout() {
  if (confirm('Log out?')) {
    logoutUser();
    window.location.href = 'login.html';
  }
};

let profilePageManager;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    profilePageManager = new ProfilePageManager();
    window.profilePageManager = profilePageManager;
  });
} else {
  profilePageManager = new ProfilePageManager();
  window.profilePageManager = profilePageManager;
}
