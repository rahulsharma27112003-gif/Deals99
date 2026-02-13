# Deals99 - Full Stack E-commerce Platform

A comprehensive e-commerce platform with Django REST Framework backend and modern frontend.

## 🚀 Features

### Backend (Django + DRF)
- **Authentication**: JWT-based authentication with refresh tokens
- **Products Management**: CRUD operations for products, categories, subcategories
- **User Management**: User profiles, cart, wishlist
- **Order Management**: Order creation, status tracking
- **Admin Dashboard**: Complete admin panel with statistics
- **Reviews & Ratings**: Product reviews and ratings system
- **File Upload**: Image upload for products and banners
- **API Documentation**: RESTful API with proper serialization

### Frontend
- **Responsive Design**: Mobile-first approach with Bootstrap 5
- **Modern UI/UX**: Clean, professional interface
- **Real-time Updates**: Dynamic content loading
- **Shopping Cart**: Persistent cart with backend sync
- **Wishlist**: Save favorite products
- **User Authentication**: Login, registration, profile management
- **Admin Panel**: Full-featured admin dashboard
- **Search & Filters**: Advanced product search and filtering
- **Order Tracking**: View order history and status

## 🛠️ Technology Stack

### Backend
- **Django 4.2.7**: Web framework
- **Django REST Framework**: API framework
- **JWT Authentication**: Secure token-based auth
- **SQLite**: Database (easily configurable for PostgreSQL/MySQL)
- **Pillow**: Image processing
- **CORS Headers**: Cross-origin resource sharing

### Frontend
- **HTML5/CSS3**: Modern web standards
- **JavaScript ES6+**: Modern JavaScript features
- **Bootstrap 5**: Responsive CSS framework
- **Font Awesome**: Icon library
- **Quill.js**: Rich text editor

## 📦 Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js (for frontend development)
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deals99-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations and setup**
   ```bash
   python setup.py
   ```

5. **Start the development server**
   ```bash
   python run_server.py
   ```

   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Open in browser**
   - Simply open `index.html` in your browser
   - Or use a local server:
   ```bash
   python -m http.server 3000
   ```

## 🔧 Configuration

### Backend Configuration

Create a `.env` file in the backend directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### API Endpoints

The API is available at `http://localhost:8000/api/`

#### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration

#### Products
- `GET /api/products/` - List all products
- `GET /api/products/{id}/` - Get product details
- `POST /api/products/` - Create product (admin)
- `PUT /api/products/{id}/` - Update product (admin)
- `DELETE /api/products/{id}/` - Delete product (admin)

#### Categories
- `GET /api/categories/` - List categories
- `GET /api/subcategories/` - List subcategories

#### Cart & Wishlist
- `GET /api/cart/` - Get user cart
- `POST /api/cart/` - Add to cart
- `PUT /api/cart/{id}/` - Update cart item
- `DELETE /api/cart/{id}/` - Remove from cart

#### Orders
- `GET /api/orders/` - Get user orders
- `POST /api/orders/create_from_cart/` - Create order from cart

#### Admin
- `GET /api/dashboard/` - Admin dashboard stats

## 👥 Default Admin Credentials

- **Username**: admin
- **Password**: admin123
- **Email**: admin@deals99.com

## 🚀 Deployment

### Backend Deployment (Heroku)

1. **Install Heroku CLI**
2. **Create Procfile**
   ```
   web: gunicorn deals99_backend.wsgi --log-file -
   ```
3. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

### Frontend Deployment

1. **Update API_BASE in api.js**
   ```javascript
   const API_BASE = "https://your-heroku-app.herokuapp.com/api";
   ```

2. **Deploy to Netlify/Vercel**
   - Connect your repository
   - Set build command: `npm run build` (if using build tools)
   - Deploy

## 📱 Features Overview

### User Features
- ✅ User registration and login
- ✅ Product browsing with search and filters
- ✅ Shopping cart with persistent storage
- ✅ Wishlist functionality
- ✅ Order placement and tracking
- ✅ User profile management
- ✅ Product reviews and ratings

### Admin Features
- ✅ Product management (CRUD)
- ✅ Category and subcategory management
- ✅ Order management and status updates
- ✅ User management
- ✅ Dashboard with analytics
- ✅ Banner management
- ✅ Review moderation

### Technical Features
- ✅ JWT authentication
- ✅ RESTful API design
- ✅ Responsive design
- ✅ Error handling
- ✅ Loading states
- ✅ Form validation
- ✅ Image upload
- ✅ Search and filtering
- ✅ Pagination

## 🔒 Security Features

- JWT token-based authentication
- Password validation
- CORS configuration
- Input validation and sanitization
- Admin-only endpoints protection
- Secure file upload handling

## 🧪 Testing

### Backend Testing
```bash
python manage.py test
```

### Frontend Testing
- Manual testing of all user flows
- Cross-browser compatibility testing
- Mobile responsiveness testing

## 📈 Performance Optimizations

- Database query optimization
- Image compression and optimization
- Lazy loading for product images
- Caching for frequently accessed data
- API response pagination

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure CORS settings are properly configured
   - Check ALLOWED_HOSTS in settings.py

2. **Authentication Issues**
   - Verify JWT token is being sent in headers
   - Check token expiration

3. **Image Upload Issues**
   - Ensure MEDIA_ROOT and MEDIA_URL are configured
   - Check file permissions

4. **Database Issues**
   - Run migrations: `python manage.py migrate`
   - Check database permissions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, email support@deals99.com or create an issue in the repository.

## 🎯 Roadmap

- [ ] Payment gateway integration (Stripe, Razorpay)
- [ ] Email notifications
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Multi-language support
- [ ] Advanced search with Elasticsearch
- [ ] Real-time notifications
- [ ] Inventory management
- [ ] Coupon and discount system

---

**Made with ❤️ for the Deals99 community**
