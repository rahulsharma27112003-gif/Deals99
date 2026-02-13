# Deals99 Deployment Guide

This guide covers deploying the Deals99 e-commerce platform to various hosting services.

## 🚀 Quick Start

### Local Development
```bash
python start_project.py
```

This will start both backend and frontend servers automatically.

## ☁️ Cloud Deployment

### Backend Deployment (Django)

#### Option 1: Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku App**
   ```bash
   cd backend
   heroku create your-app-name
   ```

3. **Configure Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
   ```

4. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

#### Option 2: Railway

1. **Connect Repository**
   - Go to [Railway](https://railway.app)
   - Connect your GitHub repository
   - Select the backend folder

2. **Configure Environment**
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app.railway.app
   ```

3. **Deploy**
   - Railway will automatically deploy on push

#### Option 3: DigitalOcean App Platform

1. **Create App**
   - Go to DigitalOcean App Platform
   - Connect your repository
   - Select backend folder

2. **Configure Environment**
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=your-app.ondigitalocean.app
   ```

### Frontend Deployment

#### Option 1: Netlify

1. **Connect Repository**
   - Go to [Netlify](https://netlify.com)
   - Connect your GitHub repository
   - Set build command: `echo "No build required"`
   - Set publish directory: `Deals99_FullFrontend[1]/Deals99_FullFrontend[1]/Deals99_FullFrontend`

2. **Update API URL**
   - Update `API_BASE` in `api.js` to your backend URL
   - Commit and push changes

#### Option 2: Vercel

1. **Connect Repository**
   - Go to [Vercel](https://vercel.com)
   - Connect your GitHub repository
   - Set root directory: `Deals99_FullFrontend[1]/Deals99_FullFrontend[1]/Deals99_FullFrontend`

2. **Update API URL**
   - Update `API_BASE` in `api.js` to your backend URL

#### Option 3: GitHub Pages

1. **Enable GitHub Pages**
   - Go to repository settings
   - Enable GitHub Pages
   - Select source branch

2. **Update API URL**
   - Update `API_BASE` in `api.js` to your backend URL

## 🗄️ Database Options

### SQLite (Default)
- No additional setup required
- Good for development and small deployments

### PostgreSQL (Production)
1. **Install PostgreSQL**
2. **Update settings.py**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

### MySQL
1. **Install MySQL**
2. **Update settings.py**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

## 🔧 Environment Configuration

### Required Environment Variables

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:password@host:port/dbname
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Optional Environment Variables

```env
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
STATIC_URL=https://your-cdn-domain.com/static/
MEDIA_URL=https://your-cdn-domain.com/media/
```

## 📁 Static Files & Media

### For Production

1. **Install WhiteNoise**
   ```bash
   pip install whitenoise
   ```

2. **Update settings.py**
   ```python
   MIDDLEWARE = [
       'whitenoise.middleware.WhiteNoiseMiddleware',
       # ... other middleware
   ]
   
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   ```

### For CDN (Recommended)

1. **AWS S3**
   ```bash
   pip install django-storages boto3
   ```

2. **Update settings.py**
   ```python
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
   
   AWS_ACCESS_KEY_ID = 'your-access-key'
   AWS_SECRET_ACCESS_KEY = 'your-secret-key'
   AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
   AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
   ```

## 🔒 Security Checklist

### Production Security

1. **Update SECRET_KEY**
   ```python
   SECRET_KEY = os.environ.get('SECRET_KEY')
   ```

2. **Set DEBUG=False**
   ```python
   DEBUG = False
   ```

3. **Configure ALLOWED_HOSTS**
   ```python
   ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
   ```

4. **Use HTTPS**
   - Configure SSL certificates
   - Redirect HTTP to HTTPS

5. **Database Security**
   - Use strong passwords
   - Enable SSL connections
   - Regular backups

6. **API Security**
   - Rate limiting
   - Input validation
   - CORS configuration

## 📊 Monitoring & Logging

### Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Monitoring Services

1. **Sentry (Error Tracking)**
   ```bash
   pip install sentry-sdk
   ```

2. **New Relic (Performance)**
   ```bash
   pip install newrelic
   ```

## 🚀 Performance Optimization

### Database Optimization

1. **Connection Pooling**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'OPTIONS': {
               'MAX_CONNS': 20,
           }
       }
   }
   ```

2. **Query Optimization**
   - Use `select_related()` and `prefetch_related()`
   - Add database indexes
   - Use database caching

### Caching

1. **Redis Cache**
   ```bash
   pip install django-redis
   ```

2. **Update settings.py**
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django_redis.cache.RedisCache',
           'LOCATION': 'redis://127.0.0.1:6379/1',
       }
   }
   ```

## 🔄 CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "your-app-name"
        heroku_email: "your-email@example.com"
```

## 📞 Support

For deployment issues:
- Check the logs: `heroku logs --tail`
- Verify environment variables
- Test API endpoints
- Check database connectivity

## 🎯 Next Steps

After successful deployment:
1. Set up domain name
2. Configure SSL certificates
3. Set up monitoring
4. Configure backups
5. Set up staging environment
6. Implement CI/CD pipeline
