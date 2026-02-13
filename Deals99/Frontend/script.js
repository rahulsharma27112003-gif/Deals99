// ===== DEALS99 FRONTEND - COMPREHENSIVE FUNCTIONALITY =====

// Import API functions
import {
  loginUser, registerUser, logoutUser, fetchProducts, fetchFeaturedProducts,
  fetchDeals, fetchCategories, fetchCart, addToCart, removeFromCart, updateCartItem, clearCart,
  fetchWishlist, addToWishlist, removeFromWishlist, createOrder,
  fetchOrders, isAuthenticated, getCurrentUser, setCurrentUser,
  fetchUsers, updateUser, deleteUser
} from './api.js';

// ===== GLOBAL CONFIGURATION =====
const CONFIG = {
  STORAGE_KEYS: {
    CART: 'cart',
    WISHLIST: 'wishlist',
    USER: 'currentUser',
    ORDERS: 'orders',
    RECENTLY_VIEWED: 'recentlyViewed',
    ARRIVALS: 'arrivals',
    LIVE_PRODUCTS: 'liveProducts',
    TODAY_DEALS: 'today99deals',
    SPECIAL_OFFERS: 'specialOffers',
    COMBO_OFFERS: 'comboOffers',
    NEWSLETTER_SUBSCRIBERS: 'newsletterSubscribers'
  },
  ANIMATION_DURATION: 300,
  TOAST_DURATION: 3000,
  MAX_RECENT_ITEMS: 10,
  MAX_CART_ITEMS: 50,
  MAX_WISHLIST_ITEMS: 100,
  API_BASE: 'http://localhost:8000/api'
};

// ===== STORAGE MANAGER =====
class StorageManager {
  static get(key) {
  try {
    return JSON.parse(localStorage.getItem(key)) || [];
    } catch (error) {
      console.error(`StorageManager: Error reading ${key}:`, error);
    return [];
  }
}

  static set(key, value) {
    try {
  localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      console.error(`StorageManager: Error writing ${key}:`, error);
      return false;
    }
  }

  static remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error(`StorageManager: Error removing ${key}:`, error);
      return false;
    }
  }

  static clear() {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('StorageManager: Error clearing storage:', error);
      return false;
    }
  }
}

// ===== CART MANAGER =====
class CartManager {
  constructor() {
    this.items = [];
    this.init();
  }

  async init() {
    await this.loadCartFromBackend();
    this.updateCartCount();
    this.setupEventListeners();
  }

  async loadCartFromBackend() {
    if (!isAuthenticated()) {
      this.items = StorageManager.get(CONFIG.STORAGE_KEYS.CART);
      return;
    }

    try {
      const cartData = await fetchCart();
      this.items = cartData.map(item => ({
        id: item.id,
        product: item.product,
        qty: item.quantity,
        total_price: item.total_price,
        addedAt: item.created_at
      }));
    } catch (error) {
      console.error('Failed to load cart from backend:', error);
      this.items = StorageManager.get(CONFIG.STORAGE_KEYS.CART);
    }
  }

  async addItem(product) {
    try {
      if (isAuthenticated()) {
        // Add to backend
    `).join('');

    cartContainer.innerHTML = cartHTML;
  }

  setupEventListeners() {
    // Global cart event listeners
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('add-to-cart') || e.target.closest('.add-to-cart')) {
        const button = e.target.classList.contains('add-to-cart') ? e.target : e.target.closest('.add-to-cart');
        const productData = this.getProductFromButton(button);
        if (productData) {
          this.addItem(productData);
        }
      }
    });
  }

  getProductFromButton(button) {
    try {
      const productName = button.getAttribute('data-name') || button.querySelector('.product-name')?.textContent;
      const productPrice = button.getAttribute('data-price') || button.querySelector('.product-price')?.textContent;
      const productImg = button.getAttribute('data-img') || button.querySelector('.product-img')?.src;
      const productDesc = button.getAttribute('data-desc') || button.querySelector('.product-desc')?.textContent;
      const productCategory = button.getAttribute('data-category') || 'General';

      if (productName) {
        return {
          name: productName,
          price: parseFloat(productPrice?.replace(/[^\d.]/g, '')) || 0,
          img: productImg,
          desc: productDesc,
          category: productCategory
        };
      }
      return null;
    } catch (error) {
      console.error('CartManager: Error getting product data:', error);
      return null;
    }
  }
}

// ===== WISHLIST MANAGER =====
class WishlistManager {
  constructor() {
    this.items = [];
    this.init();
  }

  async init() {
    await this.loadWishlistFromBackend();
    this.updateWishlistCount();
    this.setupEventListeners();
  }

  async loadWishlistFromBackend() {
    if (!isAuthenticated()) {
      this.items = StorageManager.get(CONFIG.STORAGE_KEYS.WISHLIST);
      return;
    }

    try {
      const wishlistData = await fetchWishlist();
      this.items = wishlistData.map(item => ({
        id: item.id,
        product: item.product,
        addedAt: item.created_at
      }));
    } catch (error) {
      console.error('Failed to load wishlist from backend:', error);
      this.items = StorageManager.get(CONFIG.STORAGE_KEYS.WISHLIST);
    }
  }

  async addItem(product) {
    try {
      if (isAuthenticated()) {
        // Add to backend
        await addToWishlist(product.id || product.product?.id);
        await this.loadWishlistFromBackend();
      } else {
        // Fallback to localStorage
        const existingItem = this.items.find(item => 
          item.id === product.id || item.name === product.name
        );

        if (existingItem) {
          NotificationManager.show(product.name + ' is already in your wishlist', 'info');
          return false;
        }

        const wishlistItem = {
          ...product,
          id: product.id || ('wish_' + Date.now()),
          addedAt: new Date().toISOString()
        };

        this.items.push(wishlistItem);

        // Limit wishlist items
        if (this.items.length > CONFIG.MAX_WISHLIST_ITEMS) {
          this.items = this.items.slice(-CONFIG.MAX_WISHLIST_ITEMS);
        }

        StorageManager.set(CONFIG.STORAGE_KEYS.WISHLIST, this.items);
      }

      this.updateWishlistCount();
      this.updateWishlistUI();
      
  NotificationManager.show('Added to wishlist: ' + product.name, 'success');
      return true;
    } catch (error) {
      console.error('WishlistManager: Error adding item:', error);
      NotificationManager.show('Failed to add item to wishlist', 'error');
      return false;
    }
  }

  async removeItem(productId) {
    try {
      if (isAuthenticated()) {
        await removeFromWishlist(productId);
        await this.loadWishlistFromBackend();
      } else {
        this.items = this.items.filter(item => 
          item.id !== productId && item.name !== productId
        );
        StorageManager.set(CONFIG.STORAGE_KEYS.WISHLIST, this.items);
      }
      
      this.updateWishlistCount();
      this.updateWishlistUI();
      NotificationManager.show('Item removed from wishlist', 'info');
      return true;
    } catch (error) {
      console.error('WishlistManager: Error removing item:', error);
      return false;
    }
  }

  clearWishlist() {
    try {
      this.items = [];
      StorageManager.set(CONFIG.STORAGE_KEYS.WISHLIST, this.items);
      this.updateWishlistCount();
      this.updateWishlistUI();
      
      NotificationManager.show('Wishlist cleared', 'info');
      return true;
    } catch (error) {
      console.error('WishlistManager: Error clearing wishlist:', error);
      return false;
    }
  }

  getWishlistCount() {
    return this.items.length;
  }

  updateWishlistCount() {
    const count = this.getWishlistCount();
    const wishlistBadge = document.getElementById('wishlistCount');
    if (wishlistBadge) {
      wishlistBadge.textContent = count;
      wishlistBadge.style.display = count > 0 ? 'inline-block' : 'none';
    }
  }

  updateWishlistUI() {
    // Update wishlist page if on wishlist page
    if (window.location.pathname.includes('wishlist.html')) {
      this.renderWishlistItems();
    }
  }

  renderWishlistItems() {
    const wishlistContainer = document.getElementById('wishlistItems');
    if (!wishlistContainer) return;

    if (this.items.length === 0) {
      wishlistContainer.innerHTML = 'Your wishlist is empty.';
      return;
    }

    const wishlistText = this.items.map((item, index) =>
      item.name + ' - Rs.' + (item.price || item.discounted || item.mrp || 0)
    ).join('\n');
    wishlistContainer.textContent = wishlistText;
  }

  addToCart(productId) {
    const item = this.items.find(item => 
      item.id === productId || item.name === productId
    );
    
    if (item) {
      cartManager.addItem(item);
    }
  }

  setupEventListeners() {
    // Global wishlist event listeners
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('add-to-wishlist') || e.target.closest('.add-to-wishlist')) {
        const button = e.target.classList.contains('add-to-wishlist') ? e.target : e.target.closest('.add-to-wishlist');
        const productData = this.getProductFromButton(button);
        if (productData) {
          this.addItem(productData);
        }
      }
    });
  }

  getProductFromButton(button) {
    try {
      const productName = button.getAttribute('data-name') || button.querySelector('.product-name')?.textContent;
      const productPrice = button.getAttribute('data-price') || button.querySelector('.product-price')?.textContent;
      const productImg = button.getAttribute('data-img') || button.querySelector('.product-img')?.src;
      const productDesc = button.getAttribute('data-desc') || button.querySelector('.product-desc')?.textContent;
      const productCategory = button.getAttribute('data-category') || 'General';

      if (productName) {
        return {
          name: productName,
          price: parseFloat(productPrice?.replace(/[^\d.]/g, '')) || 0,
          img: productImg,
          desc: productDesc,
          category: productCategory
        };
      }
      return null;
    } catch (error) {
      console.error('WishlistManager: Error getting product data:', error);
      return null;
    }
  }
}

// ===== USER MANAGER =====
class UserManager {
  constructor() {
    this.currentUser = getCurrentUser();
    this.init();
  }

  init() {
    this.renderAuthArea();
    this.setupEventListeners();
  }

  async login(userData) {
    try {
      const response = await loginUser(userData.username, userData.password);
      this.currentUser = response.user;
      setCurrentUser(response.user);
      localStorage.setItem('isLoggedIn', 'true');
      this.renderAuthArea();
      
  NotificationManager.show('Welcome back, ' + (response.user.first_name || response.user.username) + '!', 'success');
      return true;
    } catch (error) {
      console.error('UserManager: Error during login:', error);
      NotificationManager.show('Login failed. Please check your credentials.', 'error');
      return false;
    }
  }

  async logout() {
    try {
      logoutUser();
      this.currentUser = null;
      setCurrentUser(null);
      localStorage.removeItem('isLoggedIn');
      localStorage.removeItem('isAdminLoggedIn');
      this.renderAuthArea();
      
      NotificationManager.show('Logged out successfully', 'info');
      return true;
    } catch (error) {
      console.error('UserManager: Error during logout:', error);
      return false;
    }
  }

  async register(userData) {
    try {
      const response = await registerUser(userData);
      this.currentUser = response.user;
      setCurrentUser(response.user);
      localStorage.setItem('isLoggedIn', 'true');
      this.renderAuthArea();
      
  NotificationManager.show('Welcome to Deals99, ' + (response.user.first_name || response.user.username) + '!', 'success');
      return true;
    } catch (error) {
      console.error('UserManager: Error during registration:', error);
      NotificationManager.show('Registration failed. Please try again.', 'error');
      return false;
    }
  }

  isLoggedIn() {
    return localStorage.getItem('isLoggedIn') === 'true';
  }

  isAdmin() {
    return localStorage.getItem('isAdminLoggedIn') === 'true';
  }

  renderAuthArea() {
    const authArea = document.getElementById('authArea');
    if (!authArea) return;
    if (this.isAdmin()) {
      authArea.textContent = 'Admin logged in';
    } else if (this.isLoggedIn()) {
      const user = this.currentUser || {};
  authArea.textContent = 'Logged in as: ' + (user.name || user.email || 'User');
    } else {
      authArea.textContent = 'Not logged in';
    }
  }

  setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleLogin();
      });
    }

    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleRegister();
      });
    }

    // Admin login form
    const adminLoginForm = document.getElementById('adminLoginForm');
    if (adminLoginForm) {
      adminLoginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAdminLogin();
      });
    }
  }

  handleLogin() {
    const email = document.getElementById('email')?.value;
    const password = document.getElementById('password')?.value;

    if (!email || !password) {
      NotificationManager.show('Please fill in all fields', 'error');
      return;
    }

    // Simulate login process
    const userData = {
      name: email.split('@')[0],
      email: email,
      loginTime: new Date().toISOString()
    };

    if (this.login(userData)) {
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 1500);
    }
  }

  handleRegister() {
    const formData = new FormData(document.getElementById('registerForm'));
    const userData = {
      firstName: formData.get('firstName'),
      lastName: formData.get('lastName'),
      email: formData.get('email'),
      phone: formData.get('phone'),
      address: formData.get('address'),
      gender: formData.get('gender'),
      birthDate: formData.get('birthDate'),
      newsletter: document.getElementById('newsletter')?.checked || false,
      registrationDate: new Date().toISOString()
    };

    if (this.register(userData)) {
      setTimeout(() => {
        window.location.href = 'index.html';
      }, 2000);
    }
  }

  handleAdminLogin() {
    const username = document.getElementById('adminUsername')?.value;
    const password = document.getElementById('adminPassword')?.value;

    if (!username || !password) {
      NotificationManager.show('Please fill in all fields', 'error');
    return;
  }

    // Server-side admin authentication
    (async () => {
      try {
        const data = await loginUser(username, password);
        if (data && data.user && data.user.is_staff) {
          localStorage.setItem('isAdminLoggedIn', 'true');
          setCurrentUser(data.user);
          NotificationManager.show('Admin login successful!', 'success');
          setTimeout(() => {
            window.location.href = 'admin.html';
          }, 800);
        } else {
          NotificationManager.show('You are not an admin', 'error');
        }
      } catch (err) {
        NotificationManager.show('Invalid admin credentials!', 'error');
      }
    })();
  }
}

// ===== NOTIFICATION MANAGER =====
class NotificationManager {
  static show(message, type = 'info', duration = CONFIG.TOAST_DURATION) {
    const toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
    toastContainer.style.zIndex = '9999';
    
    const toast = document.createElement('div');
  toast.className = 'toast align-items-center text-white bg-' + (type === 'success' ? 'success' : type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'primary') + ' border-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Plain text fallback for notification
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    document.body.appendChild(toastContainer);
    
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
      if (document.body.contains(toastContainer)) {
        document.body.removeChild(toastContainer);
      }
    });
  }
}

// ===== REVIEWS MANAGER =====
class ReviewsManager {
  constructor() {
    this.reviews = StorageManager.get('productReviews');
    this.init();
  }

  init() {
    this.setupEventListeners();
  }

  addReview(productId, review) {
    try {
      if (!this.reviews[productId]) {
        this.reviews[productId] = [];
      }
      
      const newReview = {
    id: 'review_' + Date.now(),
        productId: productId,
        rating: review.rating,
        title: review.title,
        comment: review.comment,
        userName: review.userName || 'Anonymous',
        date: new Date().toISOString(),
        helpful: 0,
        reported: false
      };
      
      this.reviews[productId].unshift(newReview);
      StorageManager.set('productReviews', this.reviews);
      
      NotificationManager.show('Review submitted successfully!', 'success');
      return true;
    } catch (error) {
      console.error('ReviewsManager: Error adding review:', error);
      NotificationManager.show('Failed to submit review', 'error');
      return false;
    }
  }

  getReviews(productId) {
    return this.reviews[productId] || [];
  }

  getAverageRating(productId) {
    const reviews = this.getReviews(productId);
    if (reviews.length === 0) return 0;
    
    const totalRating = reviews.reduce((sum, review) => sum + review.rating, 0);
    return Math.round((totalRating / reviews.length) * 10) / 10;
  }

  getRatingCount(productId) {
    return this.getReviews(productId).length;
  }

  renderStarRating(rating, size = 'sm') {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    // Remove HTML star rendering, return plain text rating
    return rating + ' / 5';
  }

  renderReviewForm(productId, productName) {
    // Remove HTML review form rendering
    return 'Review form not available in plain text mode.';
  }

  renderReviews(productId) {
    const reviews = this.getReviews(productId);
    if (reviews.length === 0) {
      return 'No reviews yet. Be the first to review this product!';
    }
    return reviews.map(review =>
      'Title: ' + review.title + '\n' +
      'Rating: ' + review.rating + '\n' +
      'Comment: ' + review.comment + '\n' +
      'By: ' + review.userName + '\n' +
      'Helpful: ' + review.helpful + '\n'
    ).join('\n---\n');
  }

  markHelpful(reviewId) {
    // Find and update helpful count
    Object.keys(this.reviews).forEach(productId => {
      const review = this.reviews[productId].find(r => r.id === reviewId);
      if (review) {
        review.helpful++;
        StorageManager.set('productReviews', this.reviews);
        NotificationManager.show('Thank you for your feedback!', 'success');
      }
    });
  }

  setupEventListeners() {
    // Review form submission
    document.addEventListener('submit', (e) => {
      if (e.target.id === 'reviewForm') {
        e.preventDefault();
        this.handleReviewSubmission(e.target);
      }
    });

    // Star rating interaction
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('stars') || e.target.closest('.stars')) {
        const starsContainer = e.target.classList.contains('stars') ? e.target : e.target.closest('.stars');
        const stars = starsContainer.querySelectorAll('i');
        const clickedStar = e.target;
        
        if (clickedStar.classList.contains('far') || clickedStar.classList.contains('fas')) {
          const rating = parseInt(clickedStar.dataset.rating);
          this.setStarRating(stars, rating);
        }
      }
    });
  }

  handleReviewSubmission(form) {
    const productId = form.dataset.productId;
    const rating = parseInt(form.querySelector('.stars').dataset.selectedRating) || 0;
    const title = form.querySelector('#reviewTitle').value.trim();
    const comment = form.querySelector('#reviewComment').value.trim();

    if (rating === 0) {
      NotificationManager.show('Please select a rating', 'error');
      return;
    }

    if (!title || !comment) {
      NotificationManager.show('Please fill in all fields', 'error');
      return;
    }

    const review = {
      rating: rating,
      title: title,
      comment: comment,
      userName: 'Anonymous' // In a real app, this would be the logged-in user
    };

    if (this.addReview(productId, review)) {
      form.reset();
      this.setStarRating(form.querySelector('.stars'), 0);
      // Refresh reviews display
      const reviewsContainer = document.getElementById('reviewsContainer');
      if (reviewsContainer) {
        reviewsContainer.innerHTML = this.renderReviews(productId);
      }
    }
  }

  setStarRating(starsContainer, rating) {
    const stars = starsContainer.querySelectorAll('i');
    starsContainer.dataset.selectedRating = rating;
    
    stars.forEach((star, index) => {
      const starRating = index + 1;
      if (starRating <= rating) {
        star.className = 'fas fa-star text-warning';
  } else {
        star.className = 'far fa-star text-warning';
      }
    });

    const ratingText = starsContainer.nextElementSibling;
    if (ratingText) {
  ratingText.textContent = rating > 0 ? (rating + ' star' + (rating > 1 ? 's' : '')) : 'Select rating';
    }
  }
}

// ===== PRODUCT MANAGER =====
class ProductManager {
  constructor() {
    this.init();
  }

  async init() {
    await this.loadProductsFromBackend();
    this.setupEventListeners();
  }

  async loadProductsFromBackend() {
    try {
      // Load featured products
      const featuredProducts = await fetchFeaturedProducts();
      StorageManager.set(CONFIG.STORAGE_KEYS.ARRIVALS, featuredProducts);

      // Load deals
      const deals = await fetchDeals();
      StorageManager.set(CONFIG.STORAGE_KEYS.TODAY_DEALS, deals);

      // Load all products for general use
      const allProducts = await fetchProducts();
      StorageManager.set(CONFIG.STORAGE_KEYS.LIVE_PRODUCTS, allProducts);

      this.updateProductDisplays();
    } catch (error) {
      console.error('Failed to load products from backend:', error);
      this.loadSampleData();
    }
  }

  loadSampleData() {
    // Fallback sample data if backend is not available
    if (!StorageManager.get(CONFIG.STORAGE_KEYS.ARRIVALS).length) {
      const sampleArrivals = [
        {
          name: "Wireless Headphones",
          price: 1299,
          mrp: 1999,
          img: "https://cdn-icons-png.flaticon.com/512/1048/1048927.png",
          category: "Electronics",
          desc: "High-quality wireless headphones with noise cancellation",
          stock: 12
        },
        {
          name: "Smart Watch",
          price: 2499,
          mrp: 3999,
          img: "https://cdn-icons-png.flaticon.com/512/3134/3134810.png",
          category: "Electronics",
          desc: "Feature-rich smartwatch with health tracking",
          stock: 0
        },
        {
          name: "Custom T-Shirt",
          price: 499,
          mrp: 799,
          img: "https://cdn-icons-png.flaticon.com/512/3135/3135706.png",
          category: "Fashion",
          desc: "Personalized t-shirt with your design",
          stock: 5
        }
      ];
      StorageManager.set(CONFIG.STORAGE_KEYS.ARRIVALS, sampleArrivals);
    }

    if (!StorageManager.get(CONFIG.STORAGE_KEYS.TODAY_DEALS).length) {
      const sampleDeals = [
        {
          name: "Phone Case",
          discounted: 99,
          mrp: 299,
          img: "https://cdn-icons-png.flaticon.com/512/2921/2921822.png",
          category: "Electronics",
          desc: "Premium phone case with protection",
          stock: 0
        },
        {
          name: "Keychain",
          discounted: 99,
          mrp: 199,
          img: "https://cdn-icons-png.flaticon.com/512/3700/3700833.png",
          category: "Gifts",
          desc: "Personalized keychain for your keys",
          stock: 20
        }
      ];
      StorageManager.set(CONFIG.STORAGE_KEYS.TODAY_DEALS, sampleDeals);
    }
  }

  updateProductDisplays() {
    // Update homepage product displays
    this.renderProductGrid('featuredGrid', StorageManager.get(CONFIG.STORAGE_KEYS.ARRIVALS));
    this.renderProductGrid('dealsGrid', StorageManager.get(CONFIG.STORAGE_KEYS.TODAY_DEALS));
    this.renderProductGrid('offersGrid', StorageManager.get(CONFIG.STORAGE_KEYS.TODAY_DEALS));
    this.renderProductGrid('arrivalsGrid', StorageManager.get(CONFIG.STORAGE_KEYS.ARRIVALS));
    this.renderProductGrid('comboGrid', StorageManager.get(CONFIG.STORAGE_KEYS.TODAY_DEALS));
  }

  renderProductGrid(containerId, products) {
    const container = document.getElementById(containerId);
    if (!container || !products.length) return;

    // Plain text rendering for products with stock/availability
    const productsText = products.slice(0, 4).map(product => {
      let text = 'Product: ' + product.name + '\n';
      text += 'Price: Rs.' + (product.price || product.discounted) + '\n';
      if (product.mrp && (product.mrp > (product.price || product.discounted))) {
        text += 'MRP: Rs.' + product.mrp + '\n';
      }
      text += 'Category: ' + (product.category_name || product.category || 'General') + '\n';
      // Stock/availability indicator
      if (typeof product.stock === 'number') {
        text += 'Availability: ' + (product.stock > 0 ? 'In Stock (' + product.stock + ')' : 'Out of Stock') + '\n';
      } else {
        text += 'Availability: Unknown\n';
      }
      text += '---';
      return text;
    }).join('\n');
    container.textContent = productsText;
  }

  setupEventListeners() {
    // Product quick view
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('quick-view') || e.target.closest('.quick-view')) {
        const button = e.target.classList.contains('quick-view') ? e.target : e.target.closest('.quick-view');
        const productData = this.getProductFromButton(button);
        if (productData) {
          this.showQuickView(productData);
        }
      }
    });
  }

  getProductFromButton(button) {
    try {
      const productName = button.getAttribute('data-name') || button.querySelector('.product-name')?.textContent;
      const productPrice = button.getAttribute('data-price') || button.querySelector('.product-price')?.textContent;
      const productImg = button.getAttribute('data-img') || button.querySelector('.product-img')?.src;
      const productDesc = button.getAttribute('data-desc') || button.querySelector('.product-desc')?.textContent;
      const productCategory = button.getAttribute('data-category') || 'General';

      if (productName) {
        return {
          name: productName,
          price: parseFloat(productPrice?.replace(/[^\d.]/g, '')) || 0,
          img: productImg,
          desc: productDesc,
          category: productCategory
        };
      }
      return null;
    } catch (error) {
      console.error('ProductManager: Error getting product data:', error);
      return null;
    }
  }

  showQuickView(product) {
    // Plain text quick view
    alert('Product: ' + product.name + '\n' +
      'Price: Rs.' + (product.price || product.discounted || product.mrp) + '\n' +
      'Description: ' + (product.desc || '') + '\n' +
      (product.mrp && product.mrp > (product.price || product.discounted) ? 'MRP: Rs.' + product.mrp + '\n' : '')
    );
  }
}

// ===== MODAL MANAGER =====
class ModalManager {
  static show(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      const bsModal = new bootstrap.Modal(modal);
      bsModal.show();
    }
  }

  static hide(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      const bsModal = bootstrap.Modal.getInstance(modal);
      if (bsModal) {
        bsModal.hide();
      }
    }
  }
}

// ===== DARK MODE MANAGER =====
class DarkModeManager {
  constructor() {
    this.init();
  }

  init() {
    this.loadTheme();
    this.setupEventListeners();
  }

  loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    this.setTheme(savedTheme);
  }

  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
      themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
  }

  toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
    
  NotificationManager.show('Switched to ' + newTheme + ' mode', 'info');
  }

  setupEventListeners() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        this.toggleTheme();
      });
    }
  }
}

// ===== RECENTLY VIEWED MANAGER =====
class RecentlyViewedManager {
  constructor() {
    this.items = StorageManager.get(CONFIG.STORAGE_KEYS.RECENTLY_VIEWED);
    this.init();
  }

  init() {
    this.setupEventListeners();
  }

  addProduct(product) {
    try {
      // Remove if already exists
      this.items = this.items.filter(item => 
        item.id !== product.id && item.name !== product.name
      );
      
      // Add to beginning
      this.items.unshift({
        ...product,
        viewedAt: new Date().toISOString()
      });
      
      // Keep only recent items
      if (this.items.length > CONFIG.MAX_RECENT_ITEMS) {
        this.items = this.items.slice(0, CONFIG.MAX_RECENT_ITEMS);
      }
      
      StorageManager.set(CONFIG.STORAGE_KEYS.RECENTLY_VIEWED, this.items);
      this.updateRecentlyViewedUI();
      
      return true;
    } catch (error) {
      console.error('RecentlyViewedManager: Error adding product:', error);
      return false;
    }
  }

  getRecentlyViewed() {
    return this.items;
  }

  clearRecentlyViewed() {
    this.items = [];
    StorageManager.set(CONFIG.STORAGE_KEYS.RECENTLY_VIEWED, this.items);
    this.updateRecentlyViewedUI();
    NotificationManager.show('Recently viewed cleared', 'info');
  }

  updateRecentlyViewedUI() {
    // Update homepage recently viewed section
    const container = document.getElementById('recentlyViewedGrid');
    if (container) {
      this.renderRecentlyViewedGrid(container);
    }
  }

  renderRecentlyViewedGrid(container) {
      if (this.items.length === 0) {
        container.textContent = 'No recently viewed products';
        return;
      }
      // Plain text rendering for recently viewed
      const productsText = this.items.slice(0, 4).map(product => {
        let text = 'Product: ' + product.name + '\n';
        text += 'Price: Rs.' + (product.price || product.discounted || product.mrp || 0) + '\n';
        text += 'Category: ' + (product.category || 'General') + '\n';
        text += '---';
        return text;
      }).join('\n');
      container.textContent = productsText;

    // Plain text rendering for recently viewed
    const productsText = this.items.slice(0, 4).map(product => {
      let text = 'Product: ' + product.name + '\n';
      text += 'Price: Rs.' + (product.price || product.discounted || product.mrp || 0) + '\n';
      text += 'Category: ' + (product.category || 'General') + '\n';
      text += '---';
      return text;
    }).join('\n');
    container.textContent = productsText;
  }

  setupEventListeners() {
    // Track product views
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('view-product') || e.target.closest('.view-product')) {
        const button = e.target.classList.contains('view-product') ? e.target : e.target.closest('.view-product');
        const productData = this.getProductFromButton(button);
        if (productData) {
          this.addProduct(productData);
        }
      }
    });
  }

  getProductFromButton(button) {
    try {
      const productName = button.getAttribute('data-name') || button.querySelector('.product-name')?.textContent;
      const productPrice = button.getAttribute('data-price') || button.querySelector('.product-price')?.textContent;
      const productImg = button.getAttribute('data-img') || button.querySelector('.product-img')?.src;
      const productDesc = button.getAttribute('data-desc') || button.querySelector('.product-desc')?.textContent;
      const productCategory = button.getAttribute('data-category') || 'General';

      if (productName) {
        return {
          name: productName,
          price: parseFloat(productPrice?.replace(/[^\d.]/g, '')) || 0,
          img: productImg,
          desc: productDesc,
          category: productCategory
        };
      }
      return null;
    } catch (error) {
      console.error('RecentlyViewedManager: Error getting product data:', error);
      return null;
    }
  }
}

// ===== COUNTDOWN TIMER MANAGER =====
class CountdownManager {
  constructor() {
    this.init();
  }

  init() {
    this.setupCountdown();
  }

  setupCountdown() {
    // Set end date (24 hours from now)
    const endDate = new Date();
    endDate.setHours(endDate.getHours() + 24);
    
    const countdown = setInterval(() => {
      const now = new Date().getTime();
      const distance = endDate.getTime() - now;
      
      const days = Math.floor(distance / (1000 * 60 * 60 * 24));
      const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((distance % (1000 * 60)) / 1000);
      
      // Update countdown elements
      const daysElement = document.getElementById('days');
      const hoursElement = document.getElementById('hours');
      const minutesElement = document.getElementById('minutes');
      const secondsElement = document.getElementById('seconds');
      
      if (daysElement) daysElement.textContent = days.toString().padStart(2, '0');
      if (hoursElement) hoursElement.textContent = hours.toString().padStart(2, '0');
      if (minutesElement) minutesElement.textContent = minutes.toString().padStart(2, '0');
      if (secondsElement) secondsElement.textContent = seconds.toString().padStart(2, '0');
      
      // If countdown is finished
      if (distance < 0) {
        clearInterval(countdown);
        const countdownElement = document.getElementById('flashSaleCountdown');
        if (countdownElement) {
          countdownElement.innerHTML = '<h4>Sale Ended!</h4>';
        }
      }
    }, 1000);
  }
}

// ===== EVENT HANDLERS =====
class EventHandlers {
  static init() {
    // Newsletter subscription
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
      newsletterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleNewsletterSubscription();
      });
    }

    // Search functionality
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
      searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleSearch();
      });
    }

    // Password toggle
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('toggle-password')) {
        this.togglePassword(e.target);
      }
    });

    // Back to top button
    window.addEventListener('scroll', () => {
      this.handleScroll();
    });

    // Remove from wishlist buttons
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('remove-from-wishlist') || e.target.closest('.remove-from-wishlist')) {
        const button = e.target.classList.contains('remove-from-wishlist') ? e.target : e.target.closest('.remove-from-wishlist');
        const productId = button.getAttribute('data-id');
        if (productId) {
          wishlistManager.removeItem(productId);
          NotificationManager.show('Item removed from wishlist', 'info');
          // Reload wishlist if on wishlist page
          if (window.location.pathname.includes('wishlist.html')) {
            setTimeout(() => {
              window.location.reload();
            }, 500);
          }
        }
      }
    });
  }

  static handleNewsletterSubscription() {
    const email = document.getElementById('newsletterEmail')?.value;
    if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      let subscribers = StorageManager.get(CONFIG.STORAGE_KEYS.NEWSLETTER_SUBSCRIBERS);
      if (!subscribers.includes(email)) {
        subscribers.push(email);
        StorageManager.set(CONFIG.STORAGE_KEYS.NEWSLETTER_SUBSCRIBERS, subscribers);
      }
      NotificationManager.show('Thank you for subscribing! 🎉', 'success');
      document.getElementById('newsletterEmail').value = '';
  } else {
      NotificationManager.show('Please enter a valid email address', 'error');
    }
  }

  static handleSearch() {
    const query = document.getElementById('searchInput')?.value;
    if (query) {
      // Implement search functionality
  NotificationManager.show('Searching for: ' + query, 'info');
    }
  }

  static togglePassword(button) {
    const input = button.previousElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
  } else {
      input.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  }

  static handleScroll() {
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
      if (window.pageYOffset > 300) {
        backToTop.style.display = 'block';
      } else {
        backToTop.style.display = 'none';
      }
    }
  }
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
      // Initialize all managers
    window.cartManager = new CartManager();
    window.wishlistManager = new WishlistManager();
    window.userManager = new UserManager();
    window.productManager = new ProductManager();
    window.reviewsManager = new ReviewsManager();
    window.darkModeManager = new DarkModeManager();
    window.recentlyViewedManager = new RecentlyViewedManager();
    window.countdownManager = new CountdownManager(); // Initialize countdown manager
    
    // Initialize event handlers
    EventHandlers.init();

    // Expose managers globally
    window.StorageManager = StorageManager;
    window.NotificationManager = NotificationManager;
    window.ModalManager = ModalManager;

  console.log('Deals99 Frontend initialized successfully!');
});

// ===== GLOBAL FUNCTIONS =====
window.logout = function(type) {
  if (type === 'admin') {
    localStorage.removeItem('isAdminLoggedIn');
  } else {
    userManager.logout();
  }
  window.location.href = 'index.html';
};

window.nextStep = function() {
  // Checkout step navigation
  const currentStep = document.querySelector('.checkout-step[style*="block"]');
  const nextStep = currentStep?.nextElementSibling;
  
  if (nextStep && nextStep.classList.contains('checkout-step')) {
    currentStep.style.display = 'none';
    nextStep.style.display = 'block';
  }
};

window.prevStep = function() {
  // Checkout step navigation
  const currentStep = document.querySelector('.checkout-step[style*="block"]');
  const prevStep = currentStep?.previousElementSibling;
  
  if (prevStep && prevStep.classList.contains('checkout-step')) {
    currentStep.style.display = 'none';
    prevStep.style.display = 'block';
  }
};

// ===== ADMIN PANEL PRODUCT MANAGEMENT =====
import { addProduct, updateProduct, deleteProduct, fetchProducts } from './api.js';

function showAddProductModal() {
  document.getElementById('modalTitle').textContent = 'Add New Product';
  document.getElementById('addProductModal').style.display = 'flex';
  // Clear form fields
  document.getElementById('modal-prod-name').value = '';
  document.getElementById('modal-prod-price').value = '';
  document.getElementById('modal-prod-category').value = '';
  document.getElementById('modal-prod-stock').value = '';
  document.getElementById('modal-prod-desc-editor').innerHTML = '';
  document.getElementById('modal-prod-active').checked = true;
  document.getElementById('modal-prod-featured').checked = false;
  document.getElementById('modal-prod-images').value = '';
  document.getElementById('modal-product-image-preview').innerHTML = '';
  document.getElementById('saveProductBtn').onclick = saveProduct;
}

async function saveProduct() {
  const name = document.getElementById('modal-prod-name').value;
  const price = parseFloat(document.getElementById('modal-prod-price').value);
  const category = document.getElementById('modal-prod-category').value;
  const stock = parseInt(document.getElementById('modal-prod-stock').value) || 0;
  const desc = document.getElementById('modal-prod-desc-editor').innerHTML;
  const active = document.getElementById('modal-prod-active').checked;
  const featured = document.getElementById('modal-prod-featured').checked;
  // For simplicity, skip image upload logic here
  const product = { name, price, category, stock, desc, active, featured };
  try {
    await addProduct(product);
    NotificationManager.show('Product added!', 'success');
    hideModal('addProductModal');
    loadProducts();
  } catch (e) {
    NotificationManager.show('Failed to add product', 'error');
  }
}

function showEditProductModal(product) {
  document.getElementById('modalTitle').textContent = 'Edit Product';
  document.getElementById('addProductModal').style.display = 'flex';
  document.getElementById('modal-prod-name').value = product.name;
  document.getElementById('modal-prod-price').value = product.price;
  document.getElementById('modal-prod-category').value = product.category;
  document.getElementById('modal-prod-stock').value = product.stock;
  document.getElementById('modal-prod-desc-editor').innerHTML = product.desc;
  document.getElementById('modal-prod-active').checked = product.active;
  document.getElementById('modal-prod-featured').checked = product.featured;
  document.getElementById('saveProductBtn').onclick = function() { saveEditProduct(product.id); };
}

async function saveEditProduct(id) {
  const name = document.getElementById('modal-prod-name').value;
  const price = parseFloat(document.getElementById('modal-prod-price').value);
  const category = document.getElementById('modal-prod-category').value;
  const stock = parseInt(document.getElementById('modal-prod-stock').value) || 0;
  const desc = document.getElementById('modal-prod-desc-editor').innerHTML;
  const active = document.getElementById('modal-prod-active').checked;
  const featured = document.getElementById('modal-prod-featured').checked;
  const product = { name, price, category, stock, desc, active, featured };
  try {
    await updateProduct(id, product);
    NotificationManager.show('Product updated!', 'success');
    hideModal('addProductModal');
    loadProducts();
  } catch (e) {
    NotificationManager.show('Failed to update product', 'error');
  }
}

async function handleDeleteProduct(id) {
  if (!confirm('Delete this product?')) return;
  try {
    await deleteProduct(id);
    NotificationManager.show('Product deleted!', 'success');
    loadProducts();
  } catch (e) {
    NotificationManager.show('Failed to delete product', 'error');
  }
}

async function loadProducts() {
  const productsList = document.getElementById('productsList');
  productsList.textContent = 'Loading...';
  try {
    const products = await fetchProducts();
    productsList.textContent = products.map(product => {
      let text = 'Product: ' + product.name + '\n';
      text += 'Price: Rs.' + product.price + '\n';
      text += 'Category: ' + product.category + '\n';
      text += '---';
      return text;
    }).join('\n');
  } catch (e) {
    productsList.textContent = 'Failed to load products';
  }
}

// ===== ADMIN PANEL ORDER MANAGEMENT =====
import { fetchOrders, updateOrder, deleteOrder } from './api.js';

async function loadOrders() {
  const ordersList = document.getElementById('ordersList');
  ordersList.textContent = 'Loading...';
  try {
    const orders = await fetchOrders();
    if (!orders.length) {
      ordersList.textContent = 'No orders found';
      return;
    }
    ordersList.textContent = orders.map(order => {
      let text = 'Order #' + order.id + ' | User: ' + (order.userEmail || order.userId) + '\n';
      text += 'Status: ' + order.status + '\n';
      text += 'Total: Rs.' + order.total + '\n';
      text += '---';
      return text;
    }).join('\n');
  } catch (e) {
    ordersList.textContent = 'Failed to load orders';
  }
}

async function handleOrderStatusChange(id, status) {
  try {
    await updateOrder(id, { status });
    NotificationManager.show('Order status updated!', 'success');
    loadOrders();
  } catch (e) {
    NotificationManager.show('Failed to update order', 'error');
  }
}

async function handleDeleteOrder(id) {
  if (!confirm('Delete this order?')) return;
  try {
    await deleteOrder(id);
    NotificationManager.show('Order deleted!', 'success');
    loadOrders();
  } catch (e) {
    NotificationManager.show('Failed to delete order', 'error');
  }
}

// ===== ADMIN PANEL USER MANAGEMENT =====

async function loadUsers() {
  const usersList = document.getElementById('usersList');
  usersList.textContent = 'Loading...';
  try {
    const users = await fetchUsers();
    if (!users.length) {
      usersList.textContent = 'No users found';
      return;
    }
    usersList.textContent = users.map(user => {
      let text = 'User: ' + (user.name || user.email) + '\n';
      text += 'Role: ' + (user.role || 'user') + '\n';
      text += 'Status: ' + user.status + '\n';
      text += '---';
      return text;
    }).join('\n');
  } catch (e) {
    usersList.textContent = 'Failed to load users';
  }
}

async function handleUserStatusChange(id, status) {
  try {
    await updateUser(id, { status });
    NotificationManager.show('User status updated!', 'success');
    loadUsers();
  } catch (e) {
    NotificationManager.show('Failed to update user', 'error');
  }
}

async function handleUserRoleChange(id, role) {
  try {
    await updateUser(id, { role });
    NotificationManager.show('User role updated!', 'success');
    loadUsers();
  } catch (e) {
    NotificationManager.show('Failed to update user', 'error');
  }
}

async function handleDeleteUser(id) {
  if (!confirm('Delete this user?')) return;
  try {
    await deleteUser(id);
    NotificationManager.show('User deleted!', 'success');
    loadUsers();
  } catch (e) {
    NotificationManager.show('Failed to delete user', 'error');
  }
}

// On admin panel load, also load orders and users
if (window.location.pathname.includes('admin.html')) {
  document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadOrders();
    loadUsers();
    document.getElementById('saveProductBtn').onclick = saveProduct;
  });
}

// ===== GLOBAL FUNCTIONS =====
function loadSampleData() {
  // Global function for index.html compatibility
  if (window.productManager) {
    window.productManager.loadSampleData();
  }
}