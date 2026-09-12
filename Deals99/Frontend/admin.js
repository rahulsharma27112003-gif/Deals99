/**
 * Deals99 Admin Panel - Comprehensive Admin Functionality
 * Manages products, categories, orders, users, banners with full CRUD operations
 */

import {
  loginUser, logoutUser, isAuthenticated, getCurrentUser, setCurrentUser, fetchCurrentUser,
  fetchDashboardStats, fetchAdminRevenue, fetchAdminTopProducts, fetchAdminLowStock,
  fetchProducts, createProduct, updateProductAdmin, deleteProductAdmin,
  fetchCategories, createCategory, updateCategory, deleteCategory,
  fetchSubcategories, createSubcategory, updateSubcategory, deleteSubcategory,
  fetchBanners, createBanner, updateBanner, deleteBanner,
  fetchOrders, fetchOrder, adminUpdateOrderStatus,
  fetchAdminUsers, fetchAdminUserDetail, updateUser, deleteUser,
  fetchAdminRefunds, getApiBase
} from './api.js';

// ===== ADMIN STATE =====
const AdminState = {
  currentTab: 'dashboard',
  allProducts: [],
  allCategories: [],
  allSubcategories: [],
  allBanners: [],
  allOrders: [],
  allUsers: [],
  allRefunds: [],
  stats: {},
  filteredProducts: [],
  selectedItems: new Set(),
};

// ===== INITIALIZATION =====
function isAdminUser(user) {
  if (!user) return false;
  const role = (user.role || '').toString().toLowerCase();
  return !!(
    user.is_superuser ||
    user.is_staff ||
    ['super_admin', 'superadmin', 'admin', 'manager', 'staff'].includes(role)
  );
}

export async function initAdminPanel() {
  const token = localStorage.getItem('access_token');
  let currentUser = getCurrentUser();

  if (token) {
    try {
      currentUser = await fetchCurrentUser();
      setCurrentUser(currentUser);
    } catch (error) {
      localStorage.removeItem('isAdminLoggedIn');
      currentUser = null;
    }
  }

  if (currentUser && isAdminUser(currentUser)) {
    showAdminPanel();
    await loadDashboard();
  } else {
    localStorage.removeItem('isAdminLoggedIn');
    showAdminLogin();
  }
}

function showAdminLogin() {
  document.getElementById('adminAuthContainer').style.display = 'block';
  document.getElementById('adminPanelSection').style.display = 'none';
  
  const loginBtn = document.getElementById('adminLoginBtn');
  const emailInput = document.getElementById('adminLoginEmail');
  const passwordInput = document.getElementById('adminLoginPassword');

  loginBtn.onclick = handleAdminLogin;
  emailInput.onkeypress = (e) => {
    if (e.key === 'Enter') handleAdminLogin();
  };
  passwordInput.onkeypress = (e) => {
    if (e.key === 'Enter') handleAdminLogin();
  };
}

function showAdminPanel() {
  document.getElementById('adminAuthContainer').style.display = 'none';
  document.getElementById('adminPanelSection').style.display = 'block';
}

window.adminLogout = async function adminLogout() {
  try {
    logoutUser();
  } catch (error) {
    console.warn('Admin logout request failed:', error);
  } finally {
    setCurrentUser(null);
    localStorage.removeItem('isAdminLoggedIn');
    if (document.getElementById('adminPanelSection')) {
      document.getElementById('adminPanelSection').style.display = 'none';
    }
    if (document.getElementById('adminAuthContainer')) {
      document.getElementById('adminAuthContainer').style.display = 'block';
    }
    window.location.reload();
  }
};

async function handleAdminLogin() {
  const email = document.getElementById('adminLoginEmail').value;
  const password = document.getElementById('adminLoginPassword').value;
  const errorDiv = document.getElementById('adminLoginError');

  if (!email || !password) {
    errorDiv.textContent = 'Please enter email and password';
    return;
  }

  try {
    errorDiv.textContent = '';
    const result = await loginUser(email, password);

    if (!isAdminUser(result.user)) {
      logoutUser();
      setCurrentUser(null);
      localStorage.removeItem('isAdminLoggedIn');
      errorDiv.textContent = 'Access denied. Admin credentials required.';
      return;
    }

    localStorage.setItem('isAdminLoggedIn', 'true');
    localStorage.setItem('access_token', result.access);
    
    showAdminPanel();
    await loadDashboard();
  } catch (error) {
    errorDiv.textContent = `Login failed: ${error.message}`;
  }
}

// ===== DASHBOARD =====
async function loadDashboard() {
  try {
    const stats = await fetchDashboardStats();
    AdminState.stats = stats;
    
    document.getElementById('count-products').textContent = stats.total_products || 0;
    document.getElementById('count-orders').textContent = stats.total_orders || 0;
    document.getElementById('count-users').textContent = stats.total_users || 0;
    document.getElementById('count-banners').textContent = stats.total_banners || 0;
    document.getElementById('count-reviews').textContent = stats.total_reviews || 0;
    document.getElementById('count-lowstock').textContent = stats.low_stock_count || 0;
    
    showToast('Dashboard loaded successfully');
  } catch (error) {
    showToast(`Error loading dashboard: ${error.message}`, 'error');
  }
}

// ===== TAB NAVIGATION =====
export async function showTab(tabName) {
  AdminState.currentTab = tabName;
  
  // Hide all tabs
  document.querySelectorAll('.admin-section').forEach(el => el.style.display = 'none');
  document.querySelectorAll('.admin-action-btn').forEach(btn => btn.style.background = '');
  
  // Show selected tab
  const tabElement = document.getElementById(`admin${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Section`);
  if (tabElement) tabElement.style.display = 'block';
  
  const tabBtn = document.getElementById(`tab-${tabName}`);
  if (tabBtn) tabBtn.style.background = '#457b9d';
  
  // Load data for tab
  switch(tabName) {
    case 'products':
      await Promise.all([loadProducts(), ensureCategoriesLoaded()]);
      break;
    case 'categories':
      await loadCategories();
      break;
    case 'subcategories':
      await Promise.all([loadSubcategories(), ensureCategoriesLoaded()]);
      break;
    case 'banners':
      await loadBanners();
      break;
    case 'orders':
      await loadOrders();
      break;
    case 'users':
      await loadUsers();
      break;
    case 'reviews':
      await loadReviews();
      break;
  }
}

async function ensureCategoriesLoaded() {
  if (!AdminState.allCategories.length) {
    await loadCategories();
  }
}

// ===== PRODUCTS SECTION =====
async function loadProducts() {
  try {
    AdminState.allProducts = await fetchProducts({ limit: 1000 });
    AdminState.filteredProducts = [...AdminState.allProducts];
    renderProductsList();
  } catch (error) {
    showToast(`Error loading products: ${error.message}`, 'error');
  }
}

function renderProductsList() {
  const container = document.getElementById('adminProductsList') || createProductsListContainer();
  container.innerHTML = '';
  
  AdminState.filteredProducts.forEach(product => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><input type="checkbox" class="product-checkbox" value="${product.id}" data-product-id="${product.id}"></td>
      <td><img src="${product.image || 'favicon.svg'}" alt="${product.name}" style="width:50px;height:50px;border-radius:4px;"></td>
      <td>${product.name}</td>
      <td>${product.category}</td>
      <td>₹${product.price}</td>
      <td><span class="${product.stock < 10 ? 'low-stock' : 'normal-stock'}">${product.stock}</span></td>
      <td>
        <button class="admin-action-btn" onclick="adminEditProduct(${product.id})">Edit</button>
        <button class="admin-action-btn remove" onclick="adminDeleteProduct(${product.id})">Delete</button>
      </td>
    `;
    container.appendChild(row);
  });
}

function createProductsListContainer() {
  const section = document.getElementById('adminProductsSection');
  const table = document.createElement('table');
  table.className = 'admin-list-table';
  table.id = 'adminProductsTable';
  table.innerHTML = `
    <thead>
      <tr>
        <th></th>
        <th>Image</th>
        <th>Name</th>
        <th>Category</th>
        <th>Price</th>
        <th>Stock</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="adminProductsList"></tbody>
  `;
  section.appendChild(table);
  return table.querySelector('tbody');
}

export async function adminEditProduct(id) {
  const product = AdminState.allProducts.find(p => p.id === id);
  if (!product) return;
  
  const newPrice = prompt(`Edit price for ${product.name}:`, product.price);
  if (newPrice === null) return;
  
  const newStock = prompt('Edit stock:', product.stock);
  if (newStock === null) return;
  
  try {
    await updateProductAdmin(id, { price: parseFloat(newPrice), stock: parseInt(newStock) });
    showToast('Product updated successfully');
    await loadProducts();
  } catch (error) {
    showToast(`Error updating product: ${error.message}`, 'error');
  }
}

export async function adminDeleteProduct(id) {
  if (!confirm('Are you sure you want to delete this product?')) return;
  
  try {
    await deleteProductAdmin(id);
    showToast('Product deleted successfully');
    await loadProducts();
  } catch (error) {
    showToast(`Error deleting product: ${error.message}`, 'error');
  }
}

function createProductModal() {
  const modal = document.createElement('div');
  modal.id = 'productModal';
  modal.className = 'modal-bg';
  modal.style.display = 'none';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="close-btn" onclick="document.getElementById('productModal').style.display='none'">×</button>
      <h3>Add New Product</h3>
      <form id="productForm" onsubmit="handleAddProduct(event)">
        <input type="text" placeholder="Product Name" id="productName" required>
        <input type="number" placeholder="Price" id="productPrice" required>
        <input type="number" placeholder="Stock" id="productStock" required>
        <textarea placeholder="Description" id="productDescription"></textarea>
        <select id="productCategory">
          <option value="">Select Category</option>
        </select>
        <button type="submit" style="background:#27ae60;color:white;border:none;padding:10px;border-radius:4px;cursor:pointer;">Add Product</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  return modal;
}

function populateModalCategorySelect(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;
  select.innerHTML = '<option value="">Select Category</option>';
  AdminState.allCategories.forEach(category => {
    const option = document.createElement('option');
    option.value = category.id;
    option.textContent = category.name || category.title || `Category ${category.id}`;
    select.appendChild(option);
  });
}

export async function showAddProductModal() {
  if (!AdminState.allCategories.length) {
    await loadCategories();
  }
  const modal = document.getElementById('productModal') || createProductModal();
  populateModalCategorySelect('productCategory');
  modal.style.display = 'flex';
}

export async function handleAddProduct(event) {
  event.preventDefault();
  
  const productData = {
    name: document.getElementById('productName').value,
    price: parseFloat(document.getElementById('productPrice').value),
    stock: parseInt(document.getElementById('productStock').value),
    description: document.getElementById('productDescription').value,
    category: parseInt(document.getElementById('productCategory').value, 10) || null,
  };
  
  try {
    await createProduct(productData);
    showToast('Product added successfully');
    document.getElementById('productModal').style.display = 'none';
    await loadProducts();
  } catch (error) {
    showToast(`Error adding product: ${error.message}`, 'error');
  }
}

export function filterProducts() {
  const search = document.getElementById('productSearch')?.value || '';
  const category = document.getElementById('productCategoryFilter')?.value || '';
  const status = document.getElementById('productStatusFilter')?.value || '';
  
  AdminState.filteredProducts = AdminState.allProducts.filter(p => {
    const matchSearch = p.name.toLowerCase().includes(search.toLowerCase());
    const matchCategory = !category || p.category === category;
    const matchStatus = !status || (status === 'active' ? p.active !== false : p.active === false);
    return matchSearch && matchCategory && matchStatus;
  });
  
  renderProductsList();
}

export function toggleSelectAllProducts(source) {
  const checkboxes = document.querySelectorAll('#adminProductsList input[type="checkbox"]');
  checkboxes.forEach(box => { box.checked = source.checked; });
}

export function bulkDeleteProducts() {
  const checked = Array.from(document.querySelectorAll('#adminProductsList input[type="checkbox"]:checked'));
  if (!checked.length) {
    showToast('No products selected', 'error');
    return;
  }
  if (!confirm(`Delete ${checked.length} selected product(s)?`)) return;
  const ids = checked.map(box => parseInt(box.dataset.productId || box.value, 10)).filter(Boolean);
  Promise.all(ids.map(id => deleteProductAdmin(id))).then(async () => {
    showToast('Selected products deleted', 'success');
    await loadProducts();
  }).catch(error => showToast(`Delete failed: ${error.message}`, 'error'));
}

export function bulkExportProducts() {
  const records = AdminState.filteredProducts.length ? AdminState.filteredProducts : AdminState.allProducts;
  if (!records.length) {
    showToast('No products to export', 'error');
    return;
  }
  const csv = [
    ['id', 'name', 'category', 'price', 'stock', 'active'].join(','),
    ...records.map(product => [product.id, product.name, product.category, product.price, product.stock, product.active].map(value => `"${String(value).replace(/"/g, '""')}"`).join(','))
  ].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'products-export.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Exported products to CSV', 'success');
}

export function triggerProductImport() {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '.csv,text/csv';
  fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      handleProductImport(file);
    }
  });
  fileInput.click();
}

export async function handleProductImport(file) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    if (!token) {
      showToast('Authentication required', 'error');
      return;
    }

    const apiBase = getApiBase();
    const response = await fetch(`${apiBase}/v1/admin/products/import-csv/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    const result = await response.json();
    if (!response.ok) {
      showToast(`Import failed: ${result.message || response.statusText}`, 'error');
      return;
    }

    const stats = result.data || {};
    showToast(`Import completed. Created: ${stats.created || 0}, Updated: ${stats.updated || 0}`, 'success');
    await loadProducts();
  } catch (error) {
    showToast(`Import failed: ${error.message}`, 'error');
  }
}

export function getSelectedProductIds() {
  return Array.from(document.querySelectorAll('#adminProductsList input[type="checkbox"]:checked'))
    .map(box => parseInt(box.dataset.productId || box.value, 10))
    .filter(Boolean);
}

export function bulkSetFeatured(value) {
  const ids = getSelectedProductIds();
  if (!ids.length) {
    showToast('No products selected', 'error');
    return;
  }
  Promise.all(ids.map(id => updateProductAdmin(id, { featured: value }).catch(() => {}))).then(async () => {
    showToast(value ? 'Marked selected products as featured' : 'Unfeatured selected products', 'success');
    await loadProducts();
  });
}

export function bulkSetActive(value) {
  const ids = getSelectedProductIds();
  if (!ids.length) {
    showToast('No products selected', 'error');
    return;
  }
  Promise.all(ids.map(id => updateProductAdmin(id, { active: value }).catch(() => {}))).then(async () => {
    showToast(value ? 'Activated selected products' : 'Deactivated selected products', 'success');
    await loadProducts();
  });
}

export function filterSubcategories() {
  const search = document.getElementById('subcategorySearch')?.value.toLowerCase() || '';
  const category = document.getElementById('subcategoryCategoryFilter')?.value || '';

  AdminState.filteredSubcategories = AdminState.allSubcategories.filter(sub => {
    const matchSearch = sub.name.toLowerCase().includes(search) || (sub.parent_category?.name || sub.parent_category || '').toLowerCase().includes(search);
    const matchCategory = !category || sub.parent_category?.name === category || sub.parent_category === category;
    return matchSearch && matchCategory;
  });
  renderSubcategoriesList();
}

// ===== CATEGORIES SECTION =====
async function loadCategories() {
  try {
    AdminState.allCategories = await fetchCategories();
    renderCategoriesList();
    populateCategoryFilters();
  } catch (error) {
    showToast(`Error loading categories: ${error.message}`, 'error');
  }
}

function renderCategoriesList() {
  const container = document.getElementById('adminCategoriesList') || createCategoriesListContainer();
  container.innerHTML = '';
  
  if (!AdminState.allCategories || AdminState.allCategories.length === 0) {
    container.innerHTML = '<tr><td colspan="3">No categories found</td></tr>';
    return;
  }
  
  AdminState.allCategories.forEach(cat => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${cat.name || cat.title}</td>
      <td>${cat.description || 'N/A'}</td>
      <td>
        <button class="admin-action-btn" onclick="adminEditCategory(${cat.id})">Edit</button>
        <button class="admin-action-btn remove" onclick="adminDeleteCategory(${cat.id})">Delete</button>
      </td>
    `;
    container.appendChild(row);
  });
}

function populateCategoryFilters() {
  const productFilter = document.getElementById('productCategoryFilter');
  const subcategoryFilter = document.getElementById('subcategoryCategoryFilter');
  const filters = [productFilter, subcategoryFilter].filter(Boolean);
  filters.forEach(dropdown => {
    dropdown.innerHTML = '<option value="">All Categories</option>' +
      AdminState.allCategories.map(cat => `<option value="${cat.name || cat.title}">${cat.name || cat.title}</option>`).join('');
  });
}

function createCategoriesListContainer() {
  const section = document.getElementById('adminCategoriesSection') || createCategoriesSection();
  const table = document.createElement('table');
  table.className = 'admin-list-table';
  table.id = 'adminCategoriesTable';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="adminCategoriesList"></tbody>
  `;
  section.appendChild(table);
  return table.querySelector('tbody');
}

function createCategoriesSection() {
  const section = document.createElement('div');
  section.id = 'adminCategoriesSection';
  section.className = 'admin-section';
  section.innerHTML = `
    <div class="section-header">
      <h3>Category Management</h3>
      <button class="admin-action-btn" onclick="showAddCategoryModal()">Add Category</button>
    </div>
  `;
  document.querySelector('.admin-container').appendChild(section);
  return section;
}

export async function showAddCategoryModal() {
  const modal = document.createElement('div');
  modal.className = 'modal-bg';
  modal.style.display = 'flex';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="close-btn" onclick="this.closest('.modal-bg').remove()">×</button>
      <h3>Add Category</h3>
      <form onsubmit="handleAddCategory(event)">
        <input type="text" placeholder="Category Name" id="catName" required>
        <textarea placeholder="Description" id="catDesc"></textarea>
        <button type="submit" style="background:#27ae60;color:white;border:none;padding:10px;border-radius:4px;cursor:pointer;width:100%;margin-top:10px;">Add</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

export async function handleAddCategory(event) {
  event.preventDefault();
  const catData = {
    name: document.getElementById('catName').value,
    description: document.getElementById('catDesc').value,
  };
  
  try {
    await createCategory(catData);
    showToast('Category added');
    event.target.closest('.modal-bg').remove();
    await loadCategories();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminEditCategory(id) {
  const name = prompt('Edit category name:');
  if (!name) return;
  
  try {
    await updateCategory(id, { name });
    showToast('Category updated');
    await loadCategories();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminDeleteCategory(id) {
  if (!confirm('Delete this category?')) return;
  
  try {
    await deleteCategory(id);
    showToast('Category deleted');
    await loadCategories();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

// ===== BANNERS SECTION =====
async function loadBanners() {
  try {
    AdminState.allBanners = await fetchBanners();
    renderBannersList();
  } catch (error) {
    showToast(`Error loading banners: ${error.message}`, 'error');
  }
}

function renderBannersList() {
  const container = document.getElementById('adminBannersList') || createBannersListContainer();
  container.innerHTML = '';
  
  AdminState.allBanners.forEach(banner => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td><img src="${banner.image}" alt="${banner.title}" style="width:80px;height:50px;object-fit:cover;border-radius:4px;"></td>
      <td>${banner.title}</td>
      <td>${banner.link_type || 'N/A'}</td>
      <td>
        <button class="admin-action-btn" onclick="adminEditBanner(${banner.id})">Edit</button>
        <button class="admin-action-btn remove" onclick="adminDeleteBanner(${banner.id})">Delete</button>
      </td>
    `;
    container.appendChild(row);
  });
}

function createBannersListContainer() {
  const section = document.getElementById('adminBannersSection') || createBannersSection();
  const table = document.createElement('table');
  table.className = 'admin-list-table';
  table.id = 'adminBannersTable';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Image</th>
        <th>Title</th>
        <th>Type</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="adminBannersList"></tbody>
  `;
  section.appendChild(table);
  return table.querySelector('tbody');
}

function createBannersSection() {
  const section = document.createElement('div');
  section.id = 'adminBannersSection';
  section.className = 'admin-section';
  section.innerHTML = `
    <div class="section-header">
      <h3>Banner Management</h3>
      <button class="admin-action-btn" onclick="showAddBannerModal()">Add Banner</button>
    </div>
  `;
  document.querySelector('.admin-container').appendChild(section);
  return section;
}

export function showAddBannerModal() {
  const modal = document.createElement('div');
  modal.className = 'modal-bg';
  modal.style.display = 'flex';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="close-btn" onclick="this.closest('.modal-bg').remove()">×</button>
      <h3>Add Banner</h3>
      <form onsubmit="handleAddBanner(event)">
        <input type="text" placeholder="Title" id="bannerTitle" required>
        <input type="url" placeholder="Image URL" id="bannerImage" required>
        <input type="url" placeholder="Link URL" id="bannerLink">
        <button type="submit" style="background:#27ae60;color:white;border:none;padding:10px;border-radius:4px;cursor:pointer;width:100%;margin-top:10px;">Add</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
}

export async function handleAddBanner(event) {
  event.preventDefault();
  const bannerData = {
    title: document.getElementById('bannerTitle').value,
    image: document.getElementById('bannerImage').value,
    link: document.getElementById('bannerLink').value,
  };
  
  try {
    await createBanner(bannerData);
    showToast('Banner added');
    event.target.closest('.modal-bg').remove();
    await loadBanners();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminEditBanner(id) {
  const title = prompt('Edit banner title:');
  if (!title) return;
  
  try {
    await updateBanner(id, { title });
    showToast('Banner updated');
    await loadBanners();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminDeleteBanner(id) {
  if (!confirm('Delete this banner?')) return;
  
  try {
    await deleteBanner(id);
    showToast('Banner deleted');
    await loadBanners();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

// ===== ORDERS SECTION =====
async function loadOrders() {
  try {
    AdminState.allOrders = await fetchOrders();
    renderOrdersList();
  } catch (error) {
    showToast(`Error loading orders: ${error.message}`, 'error');
  }
}

function renderOrdersList() {
  const container = document.getElementById('adminOrdersList') || createOrdersListContainer();
  container.innerHTML = '';
  
  AdminState.allOrders.forEach(order => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>#${order.order_number || order.id}</td>
      <td>${order.user?.email || 'N/A'}</td>
      <td>₹${order.total_amount}</td>
      <td><span class="active">${order.status}</span></td>
      <td>
        <select onchange="adminChangeOrderStatus(${order.id}, this.value)">
          <option>${order.status}</option>
          <option value="processing">Processing</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </td>
      <td>
        <button class="admin-action-btn" onclick="viewOrder(${order.id})">View</button>
      </td>
    `;
    container.appendChild(row);
  });
}

function createOrdersListContainer() {
  const section = document.getElementById('adminOrdersSection') || createOrdersSection();
  const table = document.createElement('table');
  table.className = 'admin-list-table';
  table.id = 'adminOrdersTable';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Order #</th>
        <th>Customer</th>
        <th>Amount</th>
        <th>Status</th>
        <th>Change Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="adminOrdersList"></tbody>
  `;
  section.appendChild(table);
  return table.querySelector('tbody');
}

function createOrdersSection() {
  const section = document.createElement('div');
  section.id = 'adminOrdersSection';
  section.className = 'admin-section';
  section.innerHTML = '<div class="section-header"><h3>Order Management</h3></div>';
  document.querySelector('.admin-container').appendChild(section);
  return section;
}

export async function adminChangeOrderStatus(orderId, newStatus) {
  try {
    await adminUpdateOrderStatus(orderId, newStatus);
    showToast('Order status updated');
    await loadOrders();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function viewOrder(orderId) {
  try {
    const order = await fetchOrder(orderId);
    alert(`Order #${order.order_number}\nTotal: ₹${order.total_amount}\nStatus: ${order.status}\nItems: ${order.items?.length || 0}`);
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

// ===== USERS SECTION =====
async function loadUsers() {
  try {
    AdminState.allUsers = await fetchAdminUsers();
    renderUsersList();
  } catch (error) {
    showToast(`Error loading users: ${error.message}`, 'error');
  }
}

function renderUsersList() {
  const container = document.getElementById('adminUsersList') || createUsersListContainer();
  container.innerHTML = '';
  
  AdminState.allUsers.forEach(user => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${user.email}</td>
      <td>${user.first_name || ''} ${user.last_name || ''}</td>
      <td>${user.role || 'CUSTOMER'}</td>
      <td>${user.order_count || 0}</td>
      <td>₹${user.total_spent || 0}</td>
      <td>
        <button class="admin-action-btn" onclick="adminEditUser(${user.id})">Edit</button>
        <button class="admin-action-btn remove" onclick="adminDeleteUser(${user.id})">Delete</button>
      </td>
    `;
    container.appendChild(row);
  });
}

function createUsersListContainer() {
  const section = document.getElementById('adminUsersSection') || createUsersSection();
  const table = document.createElement('table');
  table.className = 'admin-list-table';
  table.id = 'adminUsersTable';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Email</th>
        <th>Name</th>
        <th>Role</th>
        <th>Orders</th>
        <th>Spent</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="adminUsersList"></tbody>
  `;
  section.appendChild(table);
  return table.querySelector('tbody');
}

function createUsersSection() {
  const section = document.createElement('div');
  section.id = 'adminUsersSection';
  section.className = 'admin-section';
  section.innerHTML = '<div class="section-header"><h3>User Management</h3></div>';
  document.querySelector('.admin-container').appendChild(section);
  return section;
}

export async function adminEditUser(userId) {
  const newRole = prompt('Edit user role (SUPERADMIN/ADMIN/MANAGER/STAFF/CUSTOMER):', 'CUSTOMER');
  if (!newRole) return;
  
  try {
    await updateUser(userId, { role: newRole });
    showToast('User updated');
    await loadUsers();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminDeleteUser(userId) {
  if (!confirm('Delete this user? This action cannot be undone.')) return;
  
  try {
    await deleteUser(userId);
    showToast('User deleted');
    await loadUsers();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

// ===== REVIEWS SECTION =====
async function loadReviews() {
  showToast('Reviews loading...');
  // Reviews endpoint would be added to API
}

// ===== SUBCATEGORIES SECTION =====
async function loadSubcategories() {
  try {
    AdminState.allSubcategories = await fetchSubcategories();
    AdminState.filteredSubcategories = [...AdminState.allSubcategories];
    renderSubcategoriesList();
  } catch (error) {
    showToast(`Error loading subcategories: ${error.message}`, 'error');
  }
}

function renderSubcategoriesList() {
  const container = document.getElementById('adminSubcategoriesList') || createSubcategoriesListContainer();
  container.innerHTML = '';
  
  const subcategories = (AdminState.filteredSubcategories && AdminState.filteredSubcategories.length)
    ? AdminState.filteredSubcategories
    : AdminState.allSubcategories;
  
  if (!subcategories || subcategories.length === 0) {
    container.innerHTML = '<tr><td colspan="3">No subcategories found</td></tr>';
    return;
  }
  
  subcategories.forEach(subcat => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${subcat.name}</td>
      <td>${subcat.parent_category?.name || 'N/A'}</td>
      <td>
        <button class="admin-action-btn" onclick="adminEditSubcategory(${subcat.id})">Edit</button>
        <button class="admin-action-btn remove" onclick="adminDeleteSubcategory(${subcat.id})">Delete</button>
      </td>
    `;
    container.appendChild(row);
  });
}

function createSubcategoriesListContainer() {
  const section = document.getElementById('adminSubcategoriesSection') || createSubcategoriesSection();
  const table = document.createElement('table');
  table.className = 'admin-list-table';
  table.id = 'adminSubcategoriesTable';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Name</th>
        <th>Parent Category</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="adminSubcategoriesList"></tbody>
  `;
  section.appendChild(table);
  return table.querySelector('tbody');
}

function createSubcategoriesSection() {
  const section = document.createElement('div');
  section.id = 'adminSubcategoriesSection';
  section.className = 'admin-section';
  section.innerHTML = `
    <div class="section-header">
      <h3>Subcategory Management</h3>
      <button class="admin-action-btn" onclick="showAddSubcategoryModal()">Add Subcategory</button>
    </div>
  `;
  document.querySelector('.admin-container').appendChild(section);
  return section;
}

export async function showAddSubcategoryModal() {
  if (!AdminState.allCategories.length) {
    await loadCategories();
  }
  const modal = document.createElement('div');
  modal.className = 'modal-bg';
  modal.style.display = 'flex';
  modal.innerHTML = `
    <div class="modal-content">
      <button class="close-btn" onclick="this.closest('.modal-bg').remove()">×</button>
      <h3>Add Subcategory</h3>
      <form onsubmit="handleAddSubcategory(event)">
        <input type="text" placeholder="Subcategory Name" id="subcatName" required>
        <select id="parentCat" required>
          <option value="">Select Parent Category</option>
        </select>
        <button type="submit" style="background:#27ae60;color:white;border:none;padding:10px;border-radius:4px;cursor:pointer;width:100%;margin-top:10px;">Add</button>
      </form>
    </div>
  `;
  document.body.appendChild(modal);
  populateModalCategorySelect('parentCat');
}

export async function handleAddSubcategory(event) {
  event.preventDefault();
  const subcatData = {
    name: document.getElementById('subcatName').value,
    parent_category: document.getElementById('parentCat').value,
  };
  
  try {
    await createSubcategory(subcatData);
    showToast('Subcategory added');
    event.target.closest('.modal-bg').remove();
    await loadSubcategories();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminEditSubcategory(id) {
  const name = prompt('Edit subcategory name:');
  if (!name) return;
  
  try {
    await updateSubcategory(id, { name });
    showToast('Subcategory updated');
    await loadSubcategories();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

export async function adminDeleteSubcategory(id) {
  if (!confirm('Delete this subcategory?')) return;
  
  try {
    await deleteSubcategory(id);
    showToast('Subcategory deleted');
    await loadSubcategories();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
}

// ===== UTILITY FUNCTIONS =====
function showToast(message, type = 'success') {
  let toast = document.getElementById('adminToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'adminToast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  
  toast.textContent = message;
  toast.style.display = 'block';
  toast.style.background = type === 'error' ? '#e63946' : '#27ae60';
  
  setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

function hideModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'none';
  }
}

function closeImagePicker() {
  const modal = document.getElementById('imagePickerModal');
  if (modal) modal.style.display = 'none';
}

function confirmImageSelection() {
  showToast('Image selection is not implemented yet', 'error');
}

function closeCategoryModal() {
  hideModal('categoryModal');
}

function closeSubcategoryModal() {
  hideModal('subcategoryModal');
}

function handleModalImageUpload() {
  showToast('Modal image upload is not supported in this view', 'error');
}

function handleModalProductImages() {
  showToast('Product image upload is not supported in this view', 'error');
}

function saveProduct() {
  showToast('Use the admin panel controls to save products', 'error');
}

function saveSubcategory() {
  showToast('Use the admin panel controls to save subcategories', 'error');
}

function saveCategory() {
  showToast('Use the admin panel controls to save categories', 'error');
}

// ===== EXPORT FUNCTIONS FOR GLOBAL ACCESS =====
window.initAdminPanel = initAdminPanel;
window.showTab = showTab;
window.showAddProductModal = showAddProductModal;
window.handleAddProduct = handleAddProduct;
window.adminEditProduct = adminEditProduct;
window.adminDeleteProduct = adminDeleteProduct;
window.filterProducts = filterProducts;
window.toggleSelectAllProducts = toggleSelectAllProducts;
window.bulkDeleteProducts = bulkDeleteProducts;
window.bulkExportProducts = bulkExportProducts;
window.bulkSetFeatured = bulkSetFeatured;
window.bulkSetActive = bulkSetActive;
window.showAddCategoryModal = showAddCategoryModal;
window.handleAddCategory = handleAddCategory;
window.adminEditCategory = adminEditCategory;
window.adminDeleteCategory = adminDeleteCategory;
window.showAddSubcategoryModal = showAddSubcategoryModal;
window.handleAddSubcategory = handleAddSubcategory;
window.filterSubcategories = filterSubcategories;
window.showAddBannerModal = showAddBannerModal;
window.handleAddBanner = handleAddBanner;
window.hideModal = hideModal;
window.closeImagePicker = closeImagePicker;
window.confirmImageSelection = confirmImageSelection;
window.closeCategoryModal = closeCategoryModal;
window.closeSubcategoryModal = closeSubcategoryModal;
window.handleModalImageUpload = handleModalImageUpload;
window.handleModalProductImages = handleModalProductImages;
window.saveProduct = saveProduct;
window.saveSubcategory = saveSubcategory;
window.saveCategory = saveCategory;
window.adminEditBanner = adminEditBanner;
window.adminDeleteBanner = adminDeleteBanner;
window.adminChangeOrderStatus = adminChangeOrderStatus;
window.viewOrder = viewOrder;
window.adminEditUser = adminEditUser;
window.adminDeleteUser = adminDeleteUser;
window.showAddSubcategoryModal = showAddSubcategoryModal;
window.handleAddSubcategory = handleAddSubcategory;
window.adminEditSubcategory = adminEditSubcategory;
window.adminDeleteSubcategory = adminDeleteSubcategory;
