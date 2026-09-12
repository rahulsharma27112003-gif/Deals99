from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Order


class AdminDashboardPermissionsTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_superuser(
            email='super@example.com',
            password='pass1234',
        )
        self.manager = User.objects.create_user(
            email='manager@example.com',
            password='pass1234',
            is_staff=True,
        )
        self.manager.role = User.ROLE_MANAGER
        self.manager.save(update_fields=['role'])

        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='pass1234',
        )

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
            email='manager@example.com',
            password='pass1234',
            is_staff=True,
        )
        self.manager.role = User.ROLE_MANAGER
        self.manager.save(update_fields=['role'])

        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='pass1234',
        )

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

    def test_admin_can_manage_user_detail(self):
        user = User.objects.create_user(
            email='testuser@example.com',
            password='pass1234',
        )
        self.client.force_authenticate(user=self.manager)
        detail_url = f'/api/admin/users/{user.id}/'

        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], user.email)

        response = self.client.patch(detail_url, {'is_active': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=user.id)

