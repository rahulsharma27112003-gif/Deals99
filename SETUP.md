# Setup and Installation Guide for Deals99

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Deals99_Full
```

## Step 2: Set Up Python Virtual Environment

### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### On macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

## Step 3: Install Dependencies

Navigate to the backend directory and install requirements:

```bash
cd Deals99/backend
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Copy the example environment file and update it with your settings:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Then edit `.env` with your configuration:

```
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
```

### Generate a Secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 5: Initialize Database

Run migrations to set up the database:

```bash
python manage.py migrate
```

Create a superuser (admin account):

```bash
python manage.py createsuperuser
```

Load sample data (optional):

```bash
python manage.py loaddata sample_data
```

## Step 6: Create Logs Directory

The application needs a logs directory:

```bash
mkdir logs
```

## Step 7: Collect Static Files (Production)

For production deployment:

```bash
python manage.py collectstatic --noinput
```

## Step 8: Run the Development Server

```bash
python manage.py runserver
```

Or use the custom run script:

```bash
python run_server.py
```

The API will be available at: `http://localhost:8000/api/`

Admin panel: `http://localhost:8000/admin/`

---

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest api/tests/test_auth.py
```

### Run Tests with Coverage Report

```bash
pytest --cov=api --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`

### Run Only Fast Tests (Skip Slow Tests)

```bash
pytest -m "not slow"
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests Matching a Pattern

```bash
pytest -k "auth" -v
```

### Available Test Modules

- `test_auth.py` - Authentication and user profile tests
- `test_products.py` - Product listing, filtering, and search tests
- `test_cart_wishlist.py` - Shopping cart and wishlist tests
- `test_orders.py` - Order creation and management tests
- `test_models.py` - Model validation and methods tests

---

## Code Quality & Linting

### Run Linting

```bash
# Using flake8
flake8 api/

# Using pylint
pylint api/

# Using black (code formatter)
black api/
```

### Security Checks

```bash
# Bandit - security issue finder
bandit -r api/
```

---

## Email Configuration

### For Gmail:

1. Enable 2-factor authentication in your Gmail account
2. Create an App Password: https://support.google.com/accounts/answer/185833
3. In `.env`:
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   ```

### For SendGrid:

1. Create a SendGrid account: https://sendgrid.com/
2. Create an API key
3. In `.env`:
   ```
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   ```

---

## Payment Gateway Setup

### Stripe Integration

1. Create a Stripe account: https://stripe.com/
2. Get your API keys from the Stripe dashboard
3. In `.env`:
   ```
   STRIPE_PUBLIC_KEY=pk_test_your_public_key
   STRIPE_SECRET_KEY=sk_test_your_secret_key
   STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
   ```

### Razorpay Integration

1. Create a Razorpay account: https://razorpay.com/
2. Get your API keys from the Razorpay dashboard
3. In `.env`:
   ```
   RAZORPAY_KEY_ID=your_key_id
   RAZORPAY_KEY_SECRET=your_key_secret
   ```

---

## Frontend Setup

```bash
cd ../Frontend

# Option 1: Using Python's HTTP server
python -m http.server 3000

# Option 2: Using Node.js http-server
npx http-server -p 3000
```

Frontend will be available at: `http://localhost:3000/`

---

## Production Deployment

### Using Gunicorn:

```bash
gunicorn deals99_backend.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Environment Variables for Production:

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

See `DEPLOYMENT.md` for detailed deployment guides for various platforms.

---

## Troubleshooting

### Database Issues

Reset migrations:
```bash
python manage.py migrate api zero
python manage.py migrate
```

### Port Already in Use

Change the port:
```bash
python manage.py runserver 8001
```

### Missing Dependencies

Reinstall all dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### Permission Errors (Linux/macOS)

Make scripts executable:
```bash
chmod +x manage.py
chmod +x run_server.py
```

---

## Directory Structure

```
Deals99/
├── backend/
│   ├── api/
│   │   ├── migrations/
│   │   ├── templates/emails/
│   │   ├── tests/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── notifications.py
│   │   ├── payments.py
│   │   └── ...
│   ├── deals99_backend/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── logs/
│   ├── manage.py
│   ├── run_server.py
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── .env.example
│   └── ...
└── Frontend/
    ├── index.html
    ├── api.js
    ├── script.js
    ├── style.css
    └── ...
```

---

## Next Steps

1. Read `DEEP_ANALYSIS.md` for a comprehensive analysis of the project
2. Review `DEPLOYMENT.md` for deployment instructions
3. Check the admin panel at `/admin/` to manage products and orders
4. Customize templates in `api/templates/emails/` for your branding
5. Configure payment processing for your preferred gateway
6. Set up email notifications in your settings

---

## Support

For issues or questions:
- Check the logs in `logs/` directory
- Review Django error messages in console output
- Check email configuration in `.env`
- Verify database migrations are up to date
- Run tests to identify issues: `pytest -v`

---

**Happy Development! 🚀**
