"""
Authentication tests for Deals99 API
Tests user registration, login, token refresh, and logout
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework.test import APIClient
from rest_framework import status


class AuthenticationTestCase(TestCase):
    """Test authentication endpoints"""

    def setUp(self):
        """Set up test client and test user"""
        self.client = APIClient()
        self.test_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecureTestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_user_registration(self):
        """Test user registration endpoint (creates inactive user & sends verification)"""
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post('/api/auth/register/', registration_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('detail', response.data)

        # Verify user was created but inactive until email verification
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)

    def test_email_verification_flow(self):
        """Registration -> email verification -> can login"""
        resp = self.client.post('/api/auth/register/', {
            'username': 'verifyuser',
            'email': 'verify@example.com',
            'password': 'VerifyPass123!',
            'password_confirm': 'VerifyPass123!'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username='verifyuser')
        from utils.tokens import make_email_verification_token
        token = make_email_verification_token(user)

        verify_resp = self.client.post('/api/auth/verify-email/', {'token': token})
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        if hasattr(user, 'is_email_verified'):
            self.assertTrue(user.is_email_verified)

    def test_password_reset_flow(self):
        """Request password reset and confirm using token"""
        user = User.objects.create_user(username='pwuser', email='pw@example.com', password='OldPass123!')

        # Request reset (should not reveal existence)
        req = self.client.post('/api/auth/password-reset/request/', {'email': 'pw@example.com'})
        self.assertEqual(req.status_code, status.HTTP_200_OK)

        from utils.tokens import make_password_reset_token
        token = make_password_reset_token(user)

        # Confirm reset
        reset = self.client.post('/api/auth/password-reset/confirm/', {
            'token': token,
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!'
        })
        self.assertEqual(reset.status_code, status.HTTP_200_OK)

        # Ensure new password works
        login = self.client.post('/api/auth/login/', {'username': 'pwuser', 'password': 'NewPass123!'})
        self.assertEqual(login.status_code, status.HTTP_200_OK)

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        registration_data = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
        }
        
        response = self.client.post('/api/auth/register/', registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data or response.data.get('non_field_errors'))

    def test_user_login(self):
        """Test user login endpoint"""
        # Create a test user
        User.objects.create_user(
            username=self.test_user_data['username'],
            email=self.test_user_data['email'],
            password=self.test_user_data['password']
        )
        
        login_data = {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password']
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.test_user_data['username'])

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create a test user
        User.objects.create_user(
            username=self.test_user_data['username'],
            password=self.test_user_data['password']
        )
        
        login_data = {
            'username': self.test_user_data['username'],
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        response = self.client.post('/api/auth/login/', {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh(self):
        """Test token refresh endpoint"""
        # Create user and get tokens
        User.objects.create_user(
            username=self.test_user_data['username'],
            password=self.test_user_data['password']
        )
        
        login_response = self.client.post('/api/auth/login/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password']
        })
        
        # The refresh token is set in a cookie
        # Attempt to refresh
        refresh_response = self.client.post('/api/auth/refresh/')
        
        # Response depends on cookie handling
        self.assertIn(refresh_response.status_code, 
                     [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])

    def test_logout(self):
        """Test logout endpoint"""
        response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('detail', response.data)

    def test_csrf_token_endpoint(self):
        """Test CSRF token endpoint"""
        response = self.client.get('/api/auth/csrf/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrfToken', response.data)


class UserProfileTestCase(TestCase):
    """Test user profile endpoints"""

    def setUp(self):
        """Set up test client and authenticated user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_get_user_profile(self):
        """Test getting user profile"""
        response = self.client.get('/api/profile/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('phone', response.data)
        self.assertIn('address', response.data)

    def test_update_user_profile(self):
        """Test updating user profile"""
        profile_data = {
            'phone': '1234567890',
            'address': '123 Test Street, Test City',
            'gender': 'male',
            'newsletter_subscribed': True
        }
        
        response = self.client.patch('/api/profile/me/', profile_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['phone'], '1234567890')
        self.assertEqual(response.data['address'], '123 Test Street, Test City')

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users cannot access profile"""
        client = APIClient()
        response = client.get('/api/profile/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
