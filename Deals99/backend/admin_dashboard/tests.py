from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import UserProfile, Order


class AdminDashboardPermissionsTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            username='superadmin',
            email='super@example.com',
            password='pass1234',
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass1234',
            is_staff=True,
        )
        # A profile is auto-created via signals; update its role instead of creating a duplicate
        manager_profile = UserProfile.objects.get(user=self.manager)
        manager_profile.role = 'manager'
        manager_profile.save()

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass1234',
        )
        customer_profile = UserProfile.objects.get(user=self.customer)
        customer_profile.role = 'customer'
        customer_profile.save()

    def test_overview_requires_admin_role(self):
        url = '/api/admin/dashboard/'

        # Unauthenticated
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Customer should be forbidden
        self.client.force_authenticate(user=self.customer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=None)

        # Manager allowed
        self.client.force_authenticate(user=self.manager)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.client.force_authenticate(user=None)

        # Super admin allowed
        self.client.force_authenticate(user=self.super_admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=None)


class AdminOrderStatusUpdateTests(APITestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='pass1234',
            is_staff=True,
        )
        manager_profile = UserProfile.objects.get(user=self.manager)
        manager_profile.role = 'manager'
        manager_profile.save()

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='pass1234',
        )
        customer_profile = UserProfile.objects.get(user=self.customer)
        customer_profile.role = 'customer'
        customer_profile.save()

        self.order = Order.objects.create(
            user=self.customer,
            total_amount=100,
            shipping_address='Test address',
            payment_method='cod',
        )

    def test_customer_cannot_update_status(self):
        url = '/api/admin/order-status-update/'
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(url, {'order_id': self.order.id, 'status': 'shipped'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_can_update_status(self):
        url = '/api/admin/order-status-update/'
        self.client.force_authenticate(user=self.manager)
        response = self.client.post(url, {'order_id': self.order.id, 'status': 'shipped'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')

