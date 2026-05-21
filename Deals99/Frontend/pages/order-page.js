/**
 * Orders page — loads order history from /api/orders/ and supports ?orderId= deep link.
 */
import { fetchOrders, fetchOrder, isAuthenticated, logoutUser, getCurrentUser } from '../api.js';

function formatMoney(amount) {
  return `₹${Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function normalizeOrder(raw) {
  const total = parseFloat(raw.total_amount ?? raw.total ?? 0);
  const items = (raw.items || []).map((it) => ({
    name: it.product_name || it.product?.name || 'Item',
    qty: it.quantity || 1,
    price: parseFloat(it.price) || 0,
  }));
  const latestPayment = raw.payment || {};
  return {
    ...raw,
    id: raw.id,
    order_number: raw.order_number,
    orderDate: raw.created_at,
    total,
    total_amount: total,
    status: raw.status || 'pending',
    shipping_address: raw.shipping_address || '',
    payment_method: raw.payment_method || 'cod',
    payment_status: raw.payment_status || 'pending',
    payment: {
      method: latestPayment.payment_method || raw.payment_method || 'cod',
      status: latestPayment.status || raw.payment_status || 'pending',
    },
    items,
  };
}

class OrderManager {
  constructor() {
    this.orders = [];
    this.selectedOrder = null;
    this.init();
  }

  async init() {
    if (!isAuthenticated()) {
      this.renderLoginPrompt();
      return;
    }
    await this.loadOrdersFromBackend();
    this.renderOrders();
    this.updateStatistics();
    this.setupEventListeners();
    await this.openOrderFromQuery();
  }

  renderLoginPrompt() {
    const container = document.getElementById('ordersList');
    if (container) {
      container.innerHTML = `
        <div class="text-center py-5">
          <i class="fas fa-user-lock fa-4x text-muted mb-3"></i>
          <h4 class="text-muted">Sign in to view orders</h4>
          <a href="login.html" class="btn btn-primary">Login</a>
        </div>`;
    }
  }

  async loadOrdersFromBackend() {
    try {
      const rows = await fetchOrders();
      this.orders = (rows || []).map(normalizeOrder);
    } catch (error) {
      console.error('order-page: failed to load orders', error);
      this.orders = [];
    }
  }

  async openOrderFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const orderRef = params.get('orderId');
    if (!orderRef) return;

    let order = this.orders.find(
      (o) => String(o.id) === orderRef || o.order_number === orderRef
    );
    if (!order && /^\d+$/.test(orderRef)) {
      try {
        order = normalizeOrder(await fetchOrder(orderRef));
      } catch (err) {
        console.warn('order-page: could not fetch order', orderRef, err);
      }
    }
    if (order) {
      this.viewOrder(order.id);
      this.showPendingPaymentBanner(order);
    }
  }

  showPendingPaymentBanner(order) {
    try {
      const raw = sessionStorage.getItem('deals99_pending_payment');
      if (!raw) return;
      const pending = JSON.parse(raw);
      if (
        String(pending.order_id) !== String(order.id) &&
        pending.order_number !== order.order_number
      ) {
        return;
      }
      const container = document.getElementById('orderDetails');
      if (!container) return;
      let msg = '';
      if (pending.client_secret) {
        msg = `<div class="alert alert-warning small mt-2">
          <strong>Stripe payment pending.</strong> Payment intent <code>${pending.payment_intent_id || ''}</code> was created.
          Integrate Stripe.js with client secret to complete payment.
        </div>`;
      } else if (pending.razorpay_order_id) {
        msg = `<div class="alert alert-warning small mt-2">
          <strong>Razorpay payment pending.</strong> Order id: <code>${pending.razorpay_order_id}</code>
        </div>`;
      }
      if (msg) container.insertAdjacentHTML('afterbegin', msg);
    } catch (e) {
      console.warn('order-page: pending payment banner', e);
    }
  }

  renderOrders() {
    const container = document.getElementById('ordersList');
    if (!container) return;

    if (!this.orders.length) {
      container.innerHTML = `
        <div class="text-center py-5">
          <i class="fas fa-box fa-4x text-muted mb-3"></i>
          <h4 class="text-muted">No orders yet</h4>
          <p class="text-muted">Start shopping to see your orders here!</p>
          <a href="products.html" class="btn btn-primary"><i class="fas fa-shopping-bag me-2"></i>Shop Now</a>
        </div>`;
      return;
    }

    container.innerHTML = this.orders
      .map(
        (order) => `
        <div class="order-item border-bottom p-4" data-order-id="${order.id}">
          <div class="row align-items-center">
            <div class="col-md-8">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                  <h6 class="mb-1">Order #${order.order_number || order.id}</h6>
                  <small class="text-muted">Placed ${new Date(order.orderDate).toLocaleString()}</small>
                </div>
                <span class="badge bg-${this.getStatusColor(order.status)}">${(order.status || 'pending').toUpperCase()}</span>
              </div>
              <small class="text-muted">
                ${order.items.length} item(s) · Total: ${formatMoney(order.total_amount)}
                · Payment: ${(order.payment_status || 'pending').toUpperCase()}
              </small>
              <div class="order-progress mt-2">${this.getOrderProgress(order.status)}</div>
            </div>
            <div class="col-md-4 text-end">
              <button class="btn btn-outline-primary btn-sm mb-2" type="button" data-view-order="${order.id}">
                <i class="fas fa-eye me-1"></i>View Details
              </button>
              <button class="btn btn-outline-success btn-sm" type="button" data-track-order="${order.id}">
                <i class="fas fa-truck me-1"></i>Track
              </button>
            </div>
          </div>
        </div>`
      )
      .join('');
  }

  getStatusColor(status) {
    const colors = {
      pending: 'secondary',
      processing: 'info',
      shipped: 'warning',
      delivered: 'success',
      cancelled: 'danger',
    };
    return colors[status] || 'primary';
  }

  getOrderProgress(status) {
    const steps = [
      { status: 'pending', icon: 'fas fa-clock', text: 'Pending' },
      { status: 'processing', icon: 'fas fa-box', text: 'Processing' },
      { status: 'shipped', icon: 'fas fa-truck', text: 'Shipped' },
      { status: 'delivered', icon: 'fas fa-home', text: 'Delivered' },
    ];
    const order = ['pending', 'processing', 'shipped', 'delivered'];
    const current = order.indexOf(status);
    return steps
      .map((step, idx) => {
        const done = current > idx;
        const active = current === idx;
        const color = done ? 'success' : active ? 'primary' : 'muted';
        return `<span class="me-2 small text-${color}"><i class="${step.icon}"></i> ${step.text}</span>`;
      })
      .join('');
  }

  viewOrder(orderId) {
    this.selectedOrder = this.orders.find((o) => String(o.id) === String(orderId));
    this.renderOrderDetails();
  }

  renderOrderDetails() {
    const container = document.getElementById('orderDetails');
    if (!container || !this.selectedOrder) return;

    const order = this.selectedOrder;
    const itemsHtml = (order.items || [])
      .map(
        (item) => `
        <div class="d-flex justify-content-between mb-2">
          <div><small class="fw-bold">${item.name}</small><br><small class="text-muted">Qty: ${item.qty}</small></div>
          <small class="text-success">${formatMoney(item.price * item.qty)}</small>
        </div>`
      )
      .join('');

    container.innerHTML = `
      <div class="mb-3">
        <h6>Order Information</h6>
        <div class="small">
          <div class="d-flex justify-content-between"><span>Order #</span><span class="fw-bold">${order.order_number || order.id}</span></div>
          <div class="d-flex justify-content-between"><span>Date</span><span>${new Date(order.orderDate).toLocaleString()}</span></div>
          <div class="d-flex justify-content-between"><span>Status</span><span class="badge bg-${this.getStatusColor(order.status)}">${order.status.toUpperCase()}</span></div>
          <div class="d-flex justify-content-between"><span>Total</span><span class="fw-bold text-success">${formatMoney(order.total_amount)}</span></div>
        </div>
      </div>
      <div class="mb-3">
        <h6>Shipping Address</h6>
        <p class="small text-muted mb-0">${order.shipping_address || '—'}</p>
      </div>
      <div class="mb-3"><h6>Items</h6>${itemsHtml || '<p class="small text-muted">No items</p>'}</div>
      <div class="mb-3">
        <h6>Payment</h6>
        <div class="small">
          <div class="d-flex justify-content-between"><span>Method</span><span>${(order.payment?.method || order.payment_method || 'cod').toUpperCase()}</span></div>
          <div class="d-flex justify-content-between"><span>Status</span><span class="badge bg-${order.payment_status === 'completed' ? 'success' : 'warning'}">${(order.payment_status || 'pending').toUpperCase()}</span></div>
        </div>
      </div>
      <div class="d-grid gap-2">
        <button class="btn btn-outline-primary btn-sm" type="button" data-track-order="${order.id}"><i class="fas fa-truck me-2"></i>Track Order</button>
      </div>`;
  }

  trackOrder(orderId) {
    const order = this.orders.find((o) => String(o.id) === String(orderId));
    if (!order) return;
    const messages = {
      pending: 'Order received and awaiting processing',
      processing: 'Order is being prepared',
      shipped: 'Order is on the way',
      delivered: 'Order delivered',
      cancelled: 'Order was cancelled',
    };
    this.showToast(messages[order.status] || `Status: ${order.status}`, 'info');
  }

  updateStatistics() {
    const stats = { pending: 0, shipped: 0, delivered: 0, returned: 0 };
    this.orders.forEach((order) => {
      if (order.status === 'pending' || order.status === 'processing') stats.pending += 1;
      else if (order.status === 'shipped') stats.shipped += 1;
      else if (order.status === 'delivered') stats.delivered += 1;
      else if (order.status === 'cancelled') stats.returned += 1;
    });
    const set = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };
    set('pendingCount', stats.pending);
    set('shippedCount', stats.shipped);
    set('deliveredCount', stats.delivered);
    set('returnedCount', stats.returned);
  }

  setupEventListeners() {
    document.getElementById('ordersList')?.addEventListener('click', (e) => {
      const view = e.target.closest('[data-view-order]');
      const track = e.target.closest('[data-track-order]');
      if (view) this.viewOrder(view.getAttribute('data-view-order'));
      if (track) this.trackOrder(track.getAttribute('data-track-order'));
    });
    document.getElementById('orderDetails')?.addEventListener('click', (e) => {
      const track = e.target.closest('[data-track-order]');
      if (track) this.trackOrder(track.getAttribute('data-track-order'));
    });
    document.getElementById('filterBtn')?.addEventListener('click', () => this.showToast('Filter options coming soon', 'info'));
    document.getElementById('sortBtn')?.addEventListener('click', () => this.showToast('Sort options coming soon', 'info'));
  }

  showToast(message, type = 'info') {
    window.NotificationManager?.show(message, type === 'error' ? 'error' : type === 'success' ? 'success' : 'info');
  }
}

function renderAuthArea() {
  const authArea = document.getElementById('authArea');
  if (!authArea) return;
  if (isAuthenticated()) {
    const user = getCurrentUser() || {};
    const label = user.first_name || user.username || user.email || 'Account';
    authArea.innerHTML = `
      <div class="dropdown">
        <button class="btn btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown">
          <i class="fas fa-user-circle"></i> ${label}
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><a class="dropdown-item" href="profile.html"><i class="fas fa-user"></i> Profile</a></li>
          <li><a class="dropdown-item" href="order.html"><i class="fas fa-box"></i> Orders</a></li>
          <li><hr class="dropdown-divider"></li>
          <li><button class="dropdown-item text-danger" type="button" id="orderLogoutBtn"><i class="fas fa-sign-out-alt"></i> Logout</button></li>
        </ul>
      </div>`;
    document.getElementById('orderLogoutBtn')?.addEventListener('click', () => {
      logoutUser();
      window.location.href = 'login.html';
    });
  } else {
    authArea.innerHTML = `
      <a href="login.html" class="btn btn-outline-primary me-2">Login</a>
      <a href="register.html" class="btn btn-primary">Register</a>`;
  }
}

const orderManager = new OrderManager();
window.orderManager = orderManager;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderAuthArea);
} else {
  renderAuthArea();
}
