/**
 * Wishlist page — syncs with WishlistManager and /api/wishlist/ when authenticated.
 */
import { fetchFeaturedProducts, fetchProducts } from '../api.js';

function formatMoney(amount) {
  return `₹${Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function getItems() {
  const key = window.CONFIG?.STORAGE_KEYS?.WISHLIST || 'wishlist';
  return window.wishlistManager?.items || window.StorageManager?.get(key) || [];
}

function lineKey(item) {
  return item.wishlist_id || item.id || item.product_id || item.name;
}

async function waitForWishlistManager(maxMs = 5000) {
  const start = Date.now();
  while (!window.wishlistManager && Date.now() - start < maxMs) {
    await new Promise((r) => setTimeout(r, 50));
  }
  if (window.wishlistManager?.loadWishlistFromBackend) {
    await window.wishlistManager.loadWishlistFromBackend();
  }
}

function loadWishlistItems() {
  const container = document.getElementById('wishlistItems');
  if (!container) return;

  const items = getItems();
  if (items.length === 0) {
    container.innerHTML = `
      <div class="text-center py-5">
        <i class="fas fa-heart fa-4x text-muted mb-3"></i>
        <h4 class="text-muted">Your wishlist is empty</h4>
        <p class="text-muted">Start adding products to your wishlist!</p>
        <a href="products.html" class="btn btn-primary me-2"><i class="fas fa-shopping-bag me-2"></i>Browse Products</a>
        <a href="index.html" class="btn btn-outline-primary">Home</a>
      </div>`;
    return;
  }

  container.innerHTML = items
    .map((item, index) => {
      const key = lineKey(item);
      const price = parseFloat(item.price || item.discounted || item.mrp || 0);
      const mrp = parseFloat(item.mrp || 0);
      const img = item.img || item.product?.primary_image || 'favicon.svg';
      const inStock = typeof item.stock === 'number' ? item.stock > 0 : true;
      const productId = item.product_id || item.product?.id || '';

      return `
        <div class="wishlist-item border-bottom p-4" data-key="${key}">
          <div class="row align-items-center">
            <div class="col-md-1 col-2">
              <input class="form-check-input wishlist-checkbox" type="checkbox" id="wl${index}" value="${key}">
            </div>
            <div class="col-md-2 col-4">
              <img loading="lazy" src="${img}" alt="${item.name}" class="img-fluid rounded">
            </div>
            <div class="col-md-4 col-8">
              <h6 class="mb-1">${item.name}</h6>
              <p class="text-muted small mb-0">${item.desc || ''}</p>
              <div class="mt-2">
                <span class="badge bg-primary">${item.category || 'General'}</span>
                <span class="badge ${inStock ? 'bg-success' : 'bg-warning'} ms-1">${inStock ? 'In Stock' : 'Out of Stock'}</span>
              </div>
            </div>
            <div class="col-md-2 col-6 text-center">
              <span class="text-success fw-bold">${formatMoney(price)}</span>
              ${mrp > price ? `<br><small class="text-muted text-decoration-line-through">${formatMoney(mrp)}</small>` : ''}
            </div>
            <div class="col-md-3 col-6 text-end">
              <div class="btn-group-vertical btn-group-sm">
                <button class="btn btn-success btn-sm add-to-cart"
                        data-product-id="${productId}"
                        data-name="${item.name}"
                        data-price="${price}"
                        data-img="${img}"
                        data-desc="${item.desc || ''}"
                        data-category="${item.category || ''}"
                        ${!inStock ? 'disabled' : ''}>
                  <i class="fas fa-cart-plus me-1"></i>Add to Cart
                </button>
                <button class="btn btn-outline-danger btn-sm" type="button" data-remove-wishlist="${key}">
                  <i class="fas fa-trash me-1"></i>Remove
                </button>
              </div>
            </div>
          </div>
        </div>`;
    })
    .join('');

  document.querySelectorAll('.wishlist-checkbox').forEach((cb) => {
    cb.addEventListener('change', updateWishlistSummary);
  });
}

function updateWishlistSummary() {
  const items = getItems();
  const selected = document.querySelectorAll('.wishlist-checkbox:checked').length;
  const estimatedTotal = items.reduce((sum, item) => {
    return sum + parseFloat(item.price || item.discounted || item.mrp || 0);
  }, 0);

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  set('totalItems', items.length);
  set('selectedItems', selected);
  set('estimatedTotal', formatMoney(estimatedTotal));

  const addSelectedBtn = document.getElementById('addSelectedToCart');
  if (addSelectedBtn) addSelectedBtn.disabled = selected === 0;
}

window.selectAllItems = function selectAllItems() {
  const boxes = document.querySelectorAll('.wishlist-checkbox');
  const allChecked = Array.from(boxes).every((cb) => cb.checked);
  boxes.forEach((cb) => {
    cb.checked = !allChecked;
  });
  updateWishlistSummary();
};

window.addAllToCart = async function addAllToCart() {
  const cm = window.cartManager;
  if (!cm) return;
  let added = 0;
  for (const item of getItems()) {
    if (await cm.addItem(item)) added += 1;
  }
  if (added > 0 && window.NotificationManager) {
    window.NotificationManager.show(`Added ${added} items to cart`, 'success');
  }
};

window.shareWishlist = function shareWishlist() {
  const items = getItems();
  if (!items.length) {
    window.NotificationManager?.show('Your wishlist is empty', 'warning');
    return;
  }
  const shareData = {
    title: 'My Deals99 Wishlist',
    text: `Check out my wishlist with ${items.length} items!`,
    url: window.location.href,
  };
  if (navigator.share) {
    navigator.share(shareData);
  } else {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(shareData.text);
    window.open(`https://wa.me/?text=${text}%20${url}`, '_blank');
  }
};

async function loadRecommendedProducts() {
  const container = document.getElementById('recommendedProducts');
  if (!container) return;
  try {
    let products = await fetchFeaturedProducts();
    if (!products?.length) products = await fetchProducts({ page_size: 4 });
    const mapped = (products || []).slice(0, 4).map((p) =>
      window.ProductManager?.mapApiProduct ? window.ProductManager.mapApiProduct(p) : p
    );
    container.innerHTML = mapped
      .map(
        (product) => `
        <div class="col">
          <div class="card h-100">
            <div class="card-body text-center">
              <img src="${product.img}" alt="${product.name}" class="img-fluid mb-3" style="height:100px;object-fit:contain" loading="lazy">
              <h6>${product.name}</h6>
              <p class="text-success fw-bold">${formatMoney(product.price)}</p>
              <button class="btn btn-primary btn-sm add-to-cart"
                      data-product-id="${product.id}"
                      data-name="${product.name}"
                      data-price="${product.price}"
                      data-img="${product.img}"
                      data-category="${product.category_name || product.category}">
                <i class="fas fa-cart-plus"></i> Add to Cart
              </button>
            </div>
          </div>
        </div>`
      )
      .join('');
  } catch {
    container.innerHTML = '<div class="col-12 text-muted small">Recommendations unavailable.</div>';
  }
}

function bindEvents() {
  document.getElementById('wishlistItems')?.addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-remove-wishlist]');
    if (!btn || !window.wishlistManager) return;
    await window.wishlistManager.removeItem(btn.getAttribute('data-remove-wishlist'));
    loadWishlistItems();
    updateWishlistSummary();
  });

  document.getElementById('addSelectedToCart')?.addEventListener('click', async () => {
    const cm = window.cartManager;
    if (!cm) return;
    const keys = new Set([...document.querySelectorAll('.wishlist-checkbox:checked')].map((cb) => cb.value));
    let added = 0;
    for (const item of getItems()) {
      if (keys.has(lineKey(item)) && (await cm.addItem(item))) added += 1;
    }
    if (added > 0) {
      window.NotificationManager?.show(`Added ${added} selected items to cart`, 'success');
      document.querySelectorAll('.wishlist-checkbox:checked').forEach((cb) => {
        cb.checked = false;
      });
      updateWishlistSummary();
    }
  });

  document.addEventListener('wishlist:updated', () => {
    loadWishlistItems();
    updateWishlistSummary();
  });
}

async function init() {
  bindEvents();
  await waitForWishlistManager();
  loadWishlistItems();
  updateWishlistSummary();
  await loadRecommendedProducts();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
