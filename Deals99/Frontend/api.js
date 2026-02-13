const API_BASE = "http://localhost:8000/api";

// --- API Configuration ---
const API_CONFIG = {
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
};

// --- Token Management ---
class TokenManager {
  static getToken() {
    return localStorage.getItem('access_token');
  }

  static setToken(token) {
    localStorage.setItem('access_token', token);
  }

  static removeToken() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  static getAuthHeaders() {
    const token = this.getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
}

// --- API Request Helper ---
async function apiRequest(endpoint, options = {}) {
  const url = `${API_CONFIG.baseURL}${endpoint}`;
  const config = {
    ...API_CONFIG,
    ...options,
    headers: {
      ...API_CONFIG.headers,
      ...TokenManager.getAuthHeaders(),
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      // Token expired, try to refresh
      const refreshed = await refreshToken();
      if (refreshed) {
        // Retry the request with new token
        config.headers = { ...config.headers, ...TokenManager.getAuthHeaders() };
        const retryResponse = await fetch(url, config);
        if (!retryResponse.ok) throw new Error(`HTTP ${retryResponse.status}: ${retryResponse.statusText}`);
        return await retryResponse.json();
      } else {
        // Refresh failed, redirect to login
        TokenManager.removeToken();
        window.location.href = '/login.html';
        throw new Error('Authentication failed');
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Request failed:', error);
    throw error;
  }
}

// --- Token Refresh ---
async function refreshToken() {
  // Cookie-based refresh flow. Server sets refresh token as HttpOnly cookie on login/register.
  try {
    // Ensure CSRF cookie is available
    await fetch(`${API_CONFIG.baseURL}/auth/csrf/`, { credentials: 'include' });
    const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

    const response = await fetch(`${API_CONFIG.baseURL}/auth/refresh/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
      }
    });

    if (response.ok) {
      const data = await response.json();
      TokenManager.setToken(data.access);
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
  return false;
}

// --- User Auth ---
export async function loginUser(username, password) {
  const data = await apiRequest('/auth/login/', {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify({ username, password })
  });
  TokenManager.setToken(data.access);
  // Refresh token is set as HttpOnly cookie by the server; do not store it in localStorage
  return data;
}

export async function registerUser(userData) {
  const data = await apiRequest('/auth/register/', {
    method: 'POST',
    credentials: 'include',
    body: JSON.stringify(userData)
  });
  TokenManager.setToken(data.access);
  return data;
}

export function logoutUser() {
  // Call server to clear refresh cookie and blacklist token
  fetch(`${API_CONFIG.baseURL}/auth/logout/`, { method: 'POST', credentials: 'include' }).catch(() => {});
  TokenManager.removeToken();
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('isAdminLoggedIn');
}

// --- Products ---
export async function fetchProducts(params = {}) {
  const query = new URLSearchParams(params).toString();
  return await apiRequest(`/products/?${query}`);
}

export async function fetchProduct(id) {
  return await apiRequest(`/products/${id}/`);
}

export async function fetchFeaturedProducts() {
  return await apiRequest('/products/featured/');
}

export async function fetchDeals() {
  return await apiRequest('/products/deals/');
}

export async function addProduct(data) {
  return await apiRequest('/products/', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function updateProduct(id, data) {
  return await apiRequest(`/products/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteProduct(id) {
  return await apiRequest(`/products/${id}/`, {
    method: 'DELETE'
  });
}

// --- Categories ---
export async function fetchCategories() {
  return await apiRequest('/categories/');
}

export async function fetchSubcategories(categoryId = null) {
  const params = categoryId ? `?parent_category=${categoryId}` : '';
  return await apiRequest(`/subcategories/${params}`);
}

// --- Cart ---
export async function fetchCart() {
  return await apiRequest('/cart/');
}

export async function addToCart(productId, quantity = 1) {
  return await apiRequest('/cart/', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity })
  });
}

export async function updateCartItem(id, quantity) {
  return await apiRequest(`/cart/${id}/`, {
    method: 'PUT',
    body: JSON.stringify({ quantity })
  });
}

export async function removeFromCart(id) {
  return await apiRequest(`/cart/${id}/`, {
    method: 'DELETE'
  });
}

export async function clearCart() {
  return await apiRequest('/cart/clear/', {
    method: 'POST'
  });
}

export async function getCartTotal() {
  return await apiRequest('/cart/total/');
}

// --- Wishlist ---
export async function fetchWishlist() {
  return await apiRequest('/wishlist/');
}

export async function addToWishlist(productId) {
  return await apiRequest('/wishlist/', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId })
  });
}

export async function removeFromWishlist(id) {
  return await apiRequest(`/wishlist/${id}/`, {
    method: 'DELETE'
  });
}

// --- Orders ---
export async function fetchOrders() {
  return await apiRequest('/orders/');
}

export async function fetchOrder(id) {
  return await apiRequest(`/orders/${id}/`);
}

export async function createOrder(orderData) {
  return await apiRequest('/orders/create_from_cart/', {
    method: 'POST',
    body: JSON.stringify(orderData)
  });
}

export async function updateOrderStatus(id, status) {
  return await apiRequest(`/orders/${id}/update_status/`, {
    method: 'PATCH',
    body: JSON.stringify({ status })
  });
}

// --- Reviews ---
export async function fetchProductReviews(productId) {
  return await apiRequest(`/products/${productId}/reviews/`);
}

export async function addReview(productId, reviewData) {
  return await apiRequest(`/products/${productId}/add_review/`, {
    method: 'POST',
    body: JSON.stringify(reviewData)
  });
}

export async function markReviewHelpful(reviewId) {
  return await apiRequest(`/reviews/${reviewId}/mark_helpful/`, {
    method: 'POST'
  });
}

// --- Banners ---
export async function fetchBanners() {
  return await apiRequest('/banners/');
}

// --- User Profile ---
export async function fetchUserProfile() {
  return await apiRequest('/profile/me/');
}

export async function updateUserProfile(data) {
  return await apiRequest('/profile/me/', {
    method: 'PATCH',
    body: JSON.stringify(data)
  });
}

// --- Admin Dashboard ---
export async function fetchDashboardStats() {
  return await apiRequest('/dashboard/');
}

// --- Utility Functions ---
export function isAuthenticated() {
  return !!TokenManager.getToken();
}

export function getCurrentUser() {
  const userData = localStorage.getItem('user_data');
  return userData ? JSON.parse(userData) : null;
}

export function setCurrentUser(userData) {
  localStorage.setItem('user_data', JSON.stringify(userData));
}

// ===== USER MANAGEMENT =====
export async function fetchUsers() {
  return await apiRequest('/users/');
}

export async function updateUser(id, data) {
  return await apiRequest(`/users/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteUser(id) {
  return await apiRequest(`/users/${id}/`, {
    method: 'DELETE'
  });
}

// ===== ORDER MANAGEMENT =====
export async function deleteOrder(id) {
  return await apiRequest(`/orders/${id}/`, {
    method: 'DELETE'
  });
}