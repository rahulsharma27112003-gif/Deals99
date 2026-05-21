/**
 * Deals99 API client — environment-aware base URL, JWT auth, pagination helpers.
 */
function getApiBase() {
  if (typeof window !== 'undefined' && window.__DEALS99_API_BASE__) {
    return String(window.__DEALS99_API_BASE__).replace(/\/$/, '');
  }
  if (typeof window !== 'undefined' && window.location?.origin && !window.location.origin.startsWith('file:')) {
    return `${window.location.origin}/api`;
  }
  return 'http://localhost:8000/api';
}

const API_BASE = getApiBase();

const API_CONFIG = {
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
};

/** Normalize DRF paginated or admin wrapped responses to arrays/objects. */
export function unwrapPaginated(data) {
  if (data == null) return [];
  if (Array.isArray(data)) return data;
  if (data.success === true && data.data !== undefined) {
    if (Array.isArray(data.data)) return data.data;
    if (data.data?.results) return data.data.results;
    return data.data;
  }
  if (Array.isArray(data.results)) return data.results;
  return data;
}

export function unwrapObject(data) {
  if (data?.success === true && data.data !== undefined) return data.data;
  return data;
}

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
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

// --- API Request Helper ---
async function apiRequest(endpoint, options = {}) {
  const url = `${API_CONFIG.baseURL}${endpoint}`;
  const config = {
    credentials: options.credentials ?? 'include',
    ...options,
    headers: {
      ...API_CONFIG.headers,
      ...TokenManager.getAuthHeaders(),
      ...options.headers,
    },
  };

  try {
    let response = await fetch(url, config);

    if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
      const refreshed = await refreshToken();
      if (refreshed) {
        config.headers = { ...config.headers, ...TokenManager.getAuthHeaders() };
        response = await fetch(url, config);
      } else {
        TokenManager.removeToken();
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('isAdminLoggedIn');
        if (typeof window !== 'undefined' && !window.location.pathname.includes('login')) {
          window.location.href = '/login.html';
        }
        throw new Error('Authentication failed');
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const msg =
        errorData.error ||
        errorData.message ||
        errorData.detail ||
        (errorData.non_field_errors && errorData.non_field_errors[0]) ||
        `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(msg);
    }

    if (response.status === 204) return null;
    return await response.json();
  } catch (error) {
    console.error('API Request failed:', endpoint, error);
    throw error;
  }
}

async function refreshToken() {
  try {
    await fetch(`${API_CONFIG.baseURL}/auth/csrf/`, { credentials: 'include' });
    const csrfToken = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='))?.split('=')[1];

    const response = await fetch(`${API_CONFIG.baseURL}/auth/refresh/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      },
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
    body: JSON.stringify({ username, password }),
  });
  TokenManager.setToken(data.access);
  if (data.user) setCurrentUser(data.user);
  return data;
}

export async function registerUser(userData) {
  const payload = {
    username: userData.username || userData.email?.split('@')[0] || `user_${Date.now()}`,
    email: userData.email,
    first_name: userData.first_name || userData.firstName || '',
    last_name: userData.last_name || userData.lastName || '',
    password: userData.password,
    password_confirm: userData.password_confirm || userData.passwordConfirm || userData.password,
    phone: userData.phone || '',
    address: userData.address || '',
    date_of_birth: userData.date_of_birth || userData.birthDate || null,
    gender: userData.gender || '',
    newsletter_subscribed: userData.newsletter_subscribed ?? userData.newsletter ?? false,
  };
  const data = await apiRequest('/auth/register/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  TokenManager.setToken(data.access);
  if (data.user) setCurrentUser(data.user);
  return data;
}

export function logoutUser() {
  fetch(`${API_CONFIG.baseURL}/auth/logout/`, { method: 'POST', credentials: 'include' }).catch(() => {});
  TokenManager.removeToken();
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('isAdminLoggedIn');
  localStorage.removeItem('user_data');
}

// --- Products ---
export async function fetchProducts(params = {}) {
  const query = new URLSearchParams(params).toString();
  const data = await apiRequest(`/products/${query ? `?${query}` : ''}`);
  return unwrapPaginated(data);
}

export async function fetchProduct(id) {
  return unwrapObject(await apiRequest(`/products/${id}/`));
}

export async function fetchFeaturedProducts() {
  const data = await apiRequest('/products/featured/');
  return unwrapPaginated(data);
}

export async function fetchDeals() {
  const data = await apiRequest('/products/deals/');
  return unwrapPaginated(data);
}

export async function addProduct(data) {
  return apiRequest('/products/', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateProduct(id, data) {
  return apiRequest(`/products/${id}/`, { method: 'PUT', body: JSON.stringify(data) });
}

export async function deleteProduct(id) {
  return apiRequest(`/products/${id}/`, { method: 'DELETE' });
}

// --- Categories ---
export async function fetchCategories() {
  return unwrapPaginated(await apiRequest('/categories/'));
}

export async function fetchSubcategories(categoryId = null) {
  const params = categoryId ? `?parent_category=${categoryId}` : '';
  return unwrapPaginated(await apiRequest(`/subcategories/${params}`));
}

// --- Cart ---
export async function fetchCart() {
  return unwrapPaginated(await apiRequest('/cart/'));
}

export async function addToCart(productId, quantity = 1) {
  return apiRequest('/cart/', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  });
}

export async function updateCartItem(id, quantity) {
  return apiRequest(`/cart/${id}/`, {
    method: 'PUT',
    body: JSON.stringify({ quantity }),
  });
}

export async function removeFromCart(id) {
  return apiRequest(`/cart/${id}/`, { method: 'DELETE' });
}

export async function clearCart() {
  return apiRequest('/cart/clear/', { method: 'POST' });
}

export async function getCartTotal() {
  return unwrapObject(await apiRequest('/cart/total/'));
}

// --- Wishlist ---
export async function fetchWishlist() {
  return unwrapPaginated(await apiRequest('/wishlist/'));
}

export async function addToWishlist(productId) {
  return apiRequest('/wishlist/', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId }),
  });
}

export async function removeFromWishlist(id) {
  return apiRequest(`/wishlist/${id}/`, { method: 'DELETE' });
}

// --- Orders ---
export async function fetchOrders() {
  return unwrapPaginated(await apiRequest('/orders/'));
}

export async function fetchOrder(id) {
  return unwrapObject(await apiRequest(`/orders/${id}/`));
}

export async function createOrder(orderData) {
  return unwrapObject(
    await apiRequest('/orders/create_from_cart/', {
      method: 'POST',
      body: JSON.stringify(orderData),
    })
  );
}

export async function updateOrderStatus(id, status) {
  return unwrapObject(
    await apiRequest(`/orders/${id}/update_status/`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  );
}

/** Alias for legacy script imports */
export const updateOrder = updateOrderStatus;

// --- Reviews ---
export async function fetchProductReviews(productId) {
  return unwrapPaginated(await apiRequest(`/products/${productId}/reviews/`));
}

export async function addReview(productId, reviewData) {
  return apiRequest(`/products/${productId}/add_review/`, {
    method: 'POST',
    body: JSON.stringify(reviewData),
  });
}

export async function markReviewHelpful(reviewId) {
  return apiRequest(`/reviews/${reviewId}/mark_helpful/`, { method: 'POST' });
}

// --- Banners ---
export async function fetchBanners() {
  return unwrapPaginated(await apiRequest('/banners/'));
}

// --- User Profile ---
export async function fetchUserProfile() {
  return unwrapObject(await apiRequest('/profile/me/'));
}

export async function updateUserProfile(data) {
  return unwrapObject(
    await apiRequest('/profile/me/', { method: 'PATCH', body: JSON.stringify(data) })
  );
}

// --- Admin Dashboard (legacy + v1 paths) ---
export async function fetchDashboardStats() {
  try {
    return unwrapObject(await apiRequest('/admin/dashboard/'));
  } catch {
    return unwrapObject(await apiRequest('/v1/admin/dashboard/'));
  }
}

export async function fetchAdminRevenue() {
  return unwrapObject(await apiRequest('/admin/revenue/'));
}

export async function fetchAdminTopProducts(limit = 10) {
  return unwrapObject(await apiRequest(`/admin/top-products/?limit=${limit}`));
}

export async function fetchAdminLowStock(threshold = 10) {
  return unwrapObject(await apiRequest(`/admin/low-stock/?threshold=${threshold}`));
}

// --- Utility ---
export function isAuthenticated() {
  return !!TokenManager.getToken();
}

export function getCurrentUser() {
  const userData = localStorage.getItem('user_data');
  return userData ? JSON.parse(userData) : null;
}

export function setCurrentUser(userData) {
  if (userData) {
    localStorage.setItem('user_data', JSON.stringify(userData));
  } else {
    localStorage.removeItem('user_data');
  }
}

// --- Admin user management (admin_dashboard API) ---
export async function fetchUsers() {
  return unwrapPaginated(await apiRequest('/admin/users/'));
}

export async function updateUser(id, data) {
  return apiRequest(`/admin/users/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteUser(id) {
  return apiRequest(`/admin/users/${id}/`, { method: 'DELETE' });
}

export async function adminUpdateOrderStatus(orderId, status) {
  return unwrapObject(
    await apiRequest('/admin/order-status-update/', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId, status }),
    })
  );
}

export async function deleteOrder(id) {
  return apiRequest(`/orders/${id}/`, { method: 'DELETE' });
}

// --- Payments ---
export async function createPaymentIntent(orderId, paymentMethod = 'stripe') {
  return unwrapObject(
    await apiRequest('/payments/create-intent/', {
      method: 'POST',
      body: JSON.stringify({ order_id: orderId, payment_method: paymentMethod }),
    })
  );
}

export async function verifyPayment(paymentId, paymentMethod = 'stripe') {
  return unwrapObject(
    await apiRequest('/payments/verify/', {
      method: 'POST',
      body: JSON.stringify({ payment_id: paymentId, payment_method: paymentMethod }),
    })
  );
}

export { API_BASE, getApiBase, unwrapPaginated, unwrapObject };
