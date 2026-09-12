/**
 * Products listing page — loads catalog from /api/products/ and /api/categories/.
 */
import { fetchProducts, fetchCategories } from '../api.js';

const PLACEHOLDER_IMG = 'favicon.svg';

let allProducts = [];
let filteredProducts = [];

function mapProduct(p) {
  if (window.ProductManager?.mapApiProduct) {
    return window.ProductManager.mapApiProduct(p);
  }
  const price = parseFloat(p.price) || 0;
  const mrp = parseFloat(p.mrp) || price;
  return {
    id: p.id,
    product_id: p.id,
    name: p.name,
    desc: p.description || '',
    price,
    original: mrp > price ? mrp : null,
    mrp,
    category: (p.category_name || '').toLowerCase().replace(/\s+/g, '-'),
    category_name: p.category_name,
    img: p.primary_image || PLACEHOLDER_IMG,
    badge: p.featured ? 'Featured' : 'Deal',
    stock: typeof p.stock === 'number' ? p.stock : 0,
    created_at: p.created_at,
  };
}

function renderProducts() {
  const grid = document.getElementById('productsGrid');
  const status = document.getElementById('productsStatus');
  if (!grid) return;

  if (status) {
    status.textContent =
      filteredProducts.length === 0
        ? 'No products match your filters.'
        : `Showing ${filteredProducts.length} product(s)`;
  }

  if (filteredProducts.length === 0) {
    grid.innerHTML = '<div class="no-products">No products found matching your criteria.</div>';
    return;
  }

  const renderCard = window.ProductManager?.renderProductCard;
  grid.innerHTML = filteredProducts
    .map((p) => (renderCard ? renderCard(p) : `<div class="product-card">${p.name}</div>`))
    .join('');
}

function filterProducts() {
  const categoryFilter = document.getElementById('categoryFilter')?.value || '';
  const searchQuery = (document.getElementById('searchBox')?.value || '').toLowerCase();
  const sortBy = document.getElementById('sortFilter')?.value || 'name';

  filteredProducts = allProducts.filter((product) => {
    const matchesCategory =
      !categoryFilter ||
      product.category === categoryFilter ||
      (product.category_name || '').toLowerCase().replace(/\s+/g, '-') === categoryFilter;
    const matchesSearch =
      !searchQuery ||
      product.name.toLowerCase().includes(searchQuery) ||
      (product.desc || '').toLowerCase().includes(searchQuery) ||
      (product.category_name || '').toLowerCase().includes(searchQuery);
    return matchesCategory && matchesSearch;
  });

  switch (sortBy) {
    case 'price-low':
      filteredProducts.sort((a, b) => a.price - b.price);
      break;
    case 'price-high':
      filteredProducts.sort((a, b) => b.price - a.price);
      break;
    case 'name':
      filteredProducts.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'newest':
      filteredProducts.sort((a, b) => {
        const da = a.created_at ? new Date(a.created_at).getTime() : 0;
        const db = b.created_at ? new Date(b.created_at).getTime() : 0;
        return db - da;
      });
      break;
    default:
      break;
  }

  renderProducts();
}

async function populateCategoryFilter() {
  const select = document.getElementById('categoryFilter');
  if (!select) return;

  try {
    const categories = await fetchCategories();
    const active = (categories || []).filter((c) => c.active !== false);
    active.forEach((cat) => {
      const opt = document.createElement('option');
      opt.value = cat.name.toLowerCase().replace(/\s+/g, '-');
      opt.textContent = cat.name;
      select.appendChild(opt);
    });
  } catch (err) {
    console.warn('Could not load categories from API', err);
  }
}

async function loadProducts() {
  const grid = document.getElementById('productsGrid');
  if (grid) {
    grid.innerHTML = '<div class="no-products"><i class="fas fa-spinner fa-spin"></i> Loading products...</div>';
  }

  try {
    const rows = await fetchProducts({ page_size: 100 });
    allProducts = (rows || []).map(mapProduct);
    filteredProducts = [...allProducts];
    if (window.productManager) {
      window.productManager.updateProductDisplays?.();
    }
    if (window.StorageManager && window.CONFIG?.STORAGE_KEYS?.LIVE_PRODUCTS) {
      window.StorageManager.set(window.CONFIG.STORAGE_KEYS.LIVE_PRODUCTS, rows || []);
    }
    filterProducts();
  } catch (err) {
    console.error('products-page: failed to load catalog', err);
    if (grid) {
      grid.innerHTML =
        '<div class="no-products text-danger">Could not load products. Is the API running?</div>';
    }
  }
}

function bindFilters() {
  document.getElementById('categoryFilter')?.addEventListener('change', filterProducts);
  document.getElementById('sortFilter')?.addEventListener('change', filterProducts);
  document.getElementById('searchBox')?.addEventListener('input', filterProducts);
}

function applySearchFromUrl() {
  const q = new URLSearchParams(window.location.search).get('search');
  if (!q) return;
  const box = document.getElementById('searchBox');
  if (box) box.value = q;
}

async function init() {
  bindFilters();
  applySearchFromUrl();
  await populateCategoryFilter();
  await loadProducts();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
