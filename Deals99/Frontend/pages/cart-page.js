/**
 * Shopping cart page — syncs with CartManager and /api/cart/ when authenticated.
 */
import { fetchProducts, fetchFeaturedProducts, getCartTotal, isAuthenticated } from '../api.js';

function formatMoney(amount) {
  return `₹${Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function getItems() {
  const cartKey = window.CONFIG?.STORAGE_KEYS?.CART || 'cart';
  return window.cartManager?.items || window.StorageManager?.get(cartKey) || [];
}

function lineKey(item) {
  return item.id || item.product_id || item.name;
}

async function waitForCartManager(maxMs = 5000) {
  const start = Date.now();
  while (!window.cartManager && Date.now() - start < maxMs) {
    await new Promise((r) => setTimeout(r, 50));
  }
  if (window.cartManager?.loadCartFromBackend) {
    await window.cartManager.loadCartFromBackend();
  }
}

function loadCartItems() {
  const container = document.getElementById('cartItems');
  if (!container) return;

  const cartItems = getItems();

  if (cartItems.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5">
        <i class="fas fa-shopping-cart fa-4x text-muted mb-3"></i>
        <h4 class="text-muted">Your cart is empty</h4>
        <p class="text-muted">Add some products to get started!</p>
        <a href="products.html" class="btn btn-primary me-2">
          <i class="fas fa-shopping-bag me-2"></i>Browse Products
        </a>
        <a href="index.html" class="btn btn-outline-primary">Home</a>
      </div>`;
    return;
  }

  container.innerHTML = cartItems
    .map((item) => {
      const key = lineKey(item);
      const qty = item.qty || item.quantity || 1;
      const price = parseFloat(item.price || item.discounted || item.mrp || 0);
      const mrp = parseFloat(item.mrp || 0);
      const img =
        item.img ||
        item.product?.primary_image ||
        'favicon.svg';
      const name = item.name || item.product?.name || 'Product';
      const desc = item.desc || item.product?.description || '';
      const category = item.category || item.product?.category_name || 'General';
      const cartLineId = item.id;

      return `
        <div class="cart-item border-bottom p-4" data-line-id="${cartLineId || ''}">
          <div class="row align-items-center">
            <div class="col-md-2 col-4">
              <img loading="lazy" src="${img}" alt="${name}" class="img-fluid rounded">
            </div>
            <div class="col-md-4 col-8">
              <h6 class="mb-1">${name}</h6>
              <p class="text-muted small mb-0">${desc}</p>
              <div class="mt-2"><span class="badge bg-primary">${category}</span></div>
            </div>
            <div class="col-md-2 col-6">
              <div class="input-group input-group-sm">
                <button class="btn btn-outline-secondary" type="button" data-qty-dec="${key}"><i class="fas fa-minus"></i></button>
                <input type="number" class="form-control text-center cart-qty-input" value="${qty}" min="1" max="10" data-qty-key="${key}">
                <button class="btn btn-outline-secondary" type="button" data-qty-inc="${key}"><i class="fas fa-plus"></i></button>
              </div>
            </div>
            <div class="col-md-2 col-6 text-center">
              <span class="text-success fw-bold">${formatMoney(price)}</span>
              ${mrp > price ? `<br><small class="text-muted text-decoration-line-through">${formatMoney(mrp)}</small>` : ''}
            </div>
            <div class="col-md-2 col-12 text-end">
              <button class="btn btn-outline-danger btn-sm" type="button" data-remove="${key}">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          </div>
        </div>`;
    })
    .join('');
}

async function updateOrderSummary() {
  let subtotal = window.cartManager?.getCartTotal?.() ?? 0;

  if (isAuthenticated()) {
    try {
      const apiTotal = await getCartTotal();
      if (apiTotal?.total != null) {
        subtotal = parseFloat(apiTotal.total);
      }
    } catch (err) {
      console.warn('cart-page: API cart total unavailable', err);
    }
  }

  const shipping = subtotal > 499 ? 0 : 99;
  const promoCode = localStorage.getItem('appliedPromoCode') || '';
  let discount = 0;
  if (promoCode === 'DEALS10' || promoCode === 'WELCOME10') {
    discount = subtotal * 0.10;
  } else if (promoCode === 'SAVE20') {
    discount = subtotal * 0.20;
  } else if (promoCode === 'FREESHIP') {
    discount = shipping;
  }

  const tax = subtotal * 0.18;
  const total = subtotal + shipping + tax - discount;
  const shippingDisplay = shipping === 0 ? 'FREE' : formatMoney(shipping);
  const discountDisplay = discount > 0 ? `-${formatMoney(discount)}` : formatMoney(0);

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  set('subtotal', formatMoney(subtotal));
  set('shipping', shippingDisplay);
  set('tax', formatMoney(tax));
  set('discount', discountDisplay);
  set('total', formatMoney(total));

  const couponMessage = document.getElementById('couponMessage');
  if (couponMessage) {
    couponMessage.innerHTML = promoCode ? `<div class="alert alert-info">Coupon applied: ${promoCode}</div>` : '';
  }

  const checkoutBtn = document.getElementById('checkoutBtn');
  if (checkoutBtn) {
    const empty = getItems().length === 0;
    checkoutBtn.classList.toggle('disabled', empty);
    checkoutBtn.setAttribute('aria-disabled', empty ? 'true' : 'false');
  }
}

async function loadRecommendedProducts() {
  const container = document.getElementById('recommendedProducts');
  if (!container) return;

  try {
    let products = await fetchFeaturedProducts();
    if (!products?.length) {
      products = await fetchProducts({ page_size: 4 });
    }
    const mapped = (products || []).slice(0, 4).map((p) => {
      if (window.ProductManager?.mapApiProduct) {
        return window.ProductManager.mapApiProduct(p);
      }
      return {
        id: p.id,
        name: p.name,
        price: parseFloat(p.price),
        mrp: parseFloat(p.mrp) || parseFloat(p.price),
        img: p.primary_image || 'favicon.svg',
        category: p.category_name || 'General',
      };
    });

    container.innerHTML = mapped
      .map(
        (product) => `
        <div class="col">
          <div class="card h-100 product-card">
            <div class="card-body text-center">
              <img src="${product.img}" alt="${product.name}" class="img-fluid mb-3" style="height:100px;object-fit:contain" loading="lazy">
              <h6 class="card-title">${product.name}</h6>
              <p class="text-success fw-bold">${formatMoney(product.price)}</p>
              ${product.mrp > product.price ? `<p class="text-muted text-decoration-line-through small">${formatMoney(product.mrp)}</p>` : ''}
              <button class="btn btn-primary btn-sm add-to-cart"
                      data-product-id="${product.id}"
                      data-name="${product.name}"
                      data-price="${product.price}"
                      data-img="${product.img}"
                      data-category="${product.category}">
                <i class="fas fa-cart-plus me-1"></i>Add to Cart
              </button>
            </div>
          </div>
        </div>`
      )
      .join('');
  } catch (err) {
    container.innerHTML = '<div class="col-12 text-muted small">Recommendations unavailable.</div>';
  }
}

function bindCartEvents() {
  document.getElementById('cartItems')?.addEventListener('click', async (e) => {
    const dec = e.target.closest('[data-qty-dec]');
    const inc = e.target.closest('[data-qty-inc]');
    const rem = e.target.closest('[data-remove]');
    const cm = window.cartManager;
    if (!cm) return;

    if (dec) {
      const key = dec.getAttribute('data-qty-dec');
      const item = getItems().find((i) => lineKey(i) === key);
      await cm.updateQuantity(key, (item?.qty || item?.quantity || 1) - 1);
      loadCartItems();
      await updateOrderSummary();
    } else if (inc) {
      const key = inc.getAttribute('data-qty-inc');
      const item = getItems().find((i) => lineKey(i) === key);
      await cm.updateQuantity(key, (item?.qty || item?.quantity || 1) + 1);
      loadCartItems();
      await updateOrderSummary();
    } else if (rem) {
      await cm.removeItem(rem.getAttribute('data-remove'));
      loadCartItems();
      await updateOrderSummary();
    }
  });

  document.getElementById('cartItems')?.addEventListener('change', async (e) => {
    if (!e.target.classList.contains('cart-qty-input')) return;
    const key = e.target.getAttribute('data-qty-key');
    if (window.cartManager && key) {
      await window.cartManager.updateQuantity(key, e.target.value);
      loadCartItems();
      await updateOrderSummary();
    }
  });

  const checkoutBtn = document.getElementById('checkoutBtn');
  if (checkoutBtn) {
    checkoutBtn.addEventListener('click', (e) => {
      if (getItems().length === 0) {
        e.preventDefault();
        checkoutBtn.classList.add('disabled');
        checkoutBtn.setAttribute('aria-disabled', 'true');
      }
    });
  }

  document.addEventListener('cart:updated', async () => {
    console.debug('cart-page: received cart:updated event, items=', window.cartManager?.items || window.StorageManager?.get('cart'));
    loadCartItems();
    await updateOrderSummary();
  });
}

window.applyCoupon = async function applyCoupon() {
  const couponCode = document.getElementById('couponCode')?.value.trim().toUpperCase();
  const messageDiv = document.getElementById('couponMessage');
  if (!messageDiv) return;
  if (!couponCode) {
    messageDiv.innerHTML = '<div class="alert alert-warning">Please enter a coupon code</div>';
    return;
  }
  const validCoupons = {
    DEALS10: { type: 'percent', value: 10, label: '10% discount' },
    WELCOME10: { type: 'percent', value: 10, label: '10% discount' },
    SAVE20: { type: 'percent', value: 20, label: '20% discount' },
    FREESHIP: { type: 'shipping', value: 99, label: 'Free shipping' }
  };

  const coupon = validCoupons[couponCode];
  if (coupon) {
    localStorage.setItem('appliedPromoCode', couponCode);
    messageDiv.innerHTML = `<div class="alert alert-success">Coupon applied! ${coupon.label}</div>`;
    await updateOrderSummary();
    return;
  }

  localStorage.removeItem('appliedPromoCode');
  messageDiv.innerHTML = '<div class="alert alert-danger">Invalid coupon code</div>';
  await updateOrderSummary();
};

async function init() {
  bindCartEvents();
  await waitForCartManager();
  loadCartItems();
  await updateOrderSummary();
  await loadRecommendedProducts();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
