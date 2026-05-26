/**
 * Shared site header and footer for all Deals99 pages.
 */
const NAV_LINKS = [
  { id: 'home', href: 'index.html', icon: 'fa-home', label: 'Home' },
  { id: 'products', href: 'products.html', icon: 'fa-shopping-bag', label: 'Products' },
  { id: 'special-offer', href: 'special-offer.html', icon: 'fa-star', label: 'Offers' },
  { id: 'combooffers', href: 'combooffers.html', icon: 'fa-box', label: 'Combos' },
  { id: 'today99offer', href: 'today99offer.html', icon: 'fa-tag', label: '₹99 Deals' },
  { id: 'categories', href: 'categories.html', icon: 'fa-th-large', label: 'Categories' },
];

function pageKeyFromPath() {
  const file = window.location.pathname.split('/').pop() || 'index.html';
  return file.replace(/\.html$/i, '') || 'index';
}

function renderSiteHeader(activePage) {
  const navItems = NAV_LINKS.map((item) => {
    const active = item.id === activePage || (activePage === 'index' && item.id === 'home') ? ' active' : '';
    return `<li class="nav-item">
      <a class="nav-link${active}" href="${item.href}">
        <i class="fas ${item.icon}"></i> ${item.label}
      </a>
    </li>`;
  }).join('');

  return `
<nav class="navbar navbar-expand-lg navbar-light site-navbar" aria-label="Main navigation">
  <div class="container">
    <a class="navbar-brand" href="index.html">
      <i class="fas fa-tags"></i> Deals99
    </a>
    <div class="d-none d-md-flex flex-grow-1 mx-4">
      <form class="d-flex w-100" id="siteSearchForm" role="search">
        <div class="input-group">
          <input id="clientSearchInput" class="form-control" type="search"
            placeholder="Search products, deals, categories..." aria-label="Search" autocomplete="off">
          <button class="btn btn-primary" type="submit"><i class="fas fa-search"></i></button>
        </div>
      </form>
    </div>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
      aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse justify-content-end" id="navbarNav">
      <ul class="navbar-nav me-4">${navItems}</ul>
      <div class="d-flex align-items-center gap-3" id="authArea"></div>
      <div class="d-flex align-items-center gap-3 ms-3">
        <button class="theme-toggle btn btn-outline-secondary btn-sm" id="themeToggle" type="button" title="Toggle theme">
          <i class="fas fa-moon" id="themeIcon"></i>
        </button>
        <a href="cart.html" class="btn btn-outline-primary position-relative" title="Shopping Cart">
          <i class="fas fa-shopping-cart"></i>
          <span class="cart-count position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" id="cartCount" style="display:none;">0</span>
        </a>
        <a href="wishlist.html" class="btn btn-outline-danger position-relative" title="Wishlist">
          <i class="fas fa-heart"></i>
          <span class="wishlist-count position-absolute top-0 start-100 translate-middle badge rounded-pill bg-warning" id="wishlistCount" style="display:none;">0</span>
        </a>
      </div>
    </div>
  </div>
</nav>`;
}

function renderSiteFooter() {
  const year = new Date().getFullYear();
  return `
<footer class="footer site-footer">
  <div class="container">
    <div class="footer-content">
      <div class="footer-section">
        <h3><i class="fas fa-tags"></i> Deals99</h3>
        <p>Your trusted e-commerce partner for amazing deals and premium shopping experience.</p>
        <div class="d-flex gap-2 mt-3">
          <a href="#" class="btn btn-outline-light btn-sm" aria-label="Facebook"><i class="fab fa-facebook"></i></a>
          <a href="#" class="btn btn-outline-light btn-sm" aria-label="Instagram"><i class="fab fa-instagram"></i></a>
          <a href="#" class="btn btn-outline-light btn-sm" aria-label="Twitter"><i class="fab fa-twitter"></i></a>
          <a href="#" class="btn btn-outline-light btn-sm" aria-label="YouTube"><i class="fab fa-youtube"></i></a>
        </div>
      </div>
      <div class="footer-section">
        <h3>Quick Links</h3>
        <ul class="list-unstyled">
          <li><a href="index.html">Home</a></li>
          <li><a href="products.html">All Products</a></li>
          <li><a href="special-offer.html">Special Offers</a></li>
          <li><a href="combooffers.html">Combo Offers</a></li>
          <li><a href="today99offer.html">₹99 Deals</a></li>
          <li><a href="categories.html">Categories</a></li>
          <li><a href="cart.html">Shopping Cart</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Customer Service</h3>
        <ul class="list-unstyled">
          <li><a href="order.html">Track Order</a></li>
          <li><a href="account.html">My Account</a></li>
          <li><a href="profile.html">Profile</a></li>
          <li><a href="wishlist.html">Wishlist</a></li>
          <li><a href="privacy.html">Privacy Policy</a></li>
          <li><a href="terms.html">Terms &amp; Conditions</a></li>
        </ul>
      </div>
      <div class="footer-section">
        <h3>Payment Methods</h3>
        <div class="d-flex gap-2 flex-wrap">
          <i class="fab fa-cc-visa fa-2x text-white"></i>
          <i class="fab fa-cc-mastercard fa-2x text-white"></i>
          <i class="fab fa-cc-paypal fa-2x text-white"></i>
          <i class="fas fa-university fa-2x text-white"></i>
        </div>
        <p class="mt-3 small">Secure payments with SSL encryption · UPI via Razorpay</p>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="row align-items-center">
        <div class="col-md-6"><p class="mb-0">&copy; ${year} Deals99. All rights reserved.</p></div>
        <div class="col-md-6 text-md-end">
          <p class="mb-0">Made with <i class="fas fa-heart text-danger"></i> for our customers</p>
        </div>
      </div>
    </div>
  </div>
</footer>`;
}

function bindSiteSearch() {
  const form = document.getElementById('siteSearchForm');
  if (!form || form.dataset.bound) return;
  form.dataset.bound = '1';
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = (document.getElementById('clientSearchInput')?.value || '').trim();
    window.location.href = q ? `products.html?search=${encodeURIComponent(q)}` : 'products.html';
  });
}

export function initSiteLayout() {
  const headerMount = document.getElementById('site-header');
  const footerMount = document.getElementById('site-footer');
  const active = headerMount?.dataset.active || pageKeyFromPath();

  if (headerMount && !headerMount.dataset.rendered) {
    headerMount.innerHTML = renderSiteHeader(active);
    headerMount.dataset.rendered = '1';
    bindSiteSearch();
  }

  if (footerMount && !footerMount.dataset.rendered) {
    footerMount.innerHTML = renderSiteFooter();
    footerMount.dataset.rendered = '1';
  }

  document.dispatchEvent(new CustomEvent('layout:ready', { detail: { activePage: active } }));
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initSiteLayout);
} else {
  initSiteLayout();
}
