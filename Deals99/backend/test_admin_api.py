#!/usr/bin/env python
"""Quick manual test script for admin API endpoints."""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deals99_backend.config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
client = APIClient()

# Create test users
admin, _ = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'first_name': 'Admin',
        'role': User.ROLE_ADMIN,
        'is_staff': True,
    }
)
admin.set_password('adminpass')
admin.save()

manager, _ = User.objects.get_or_create(
    email='manager@example.com',
    defaults={
        'first_name': 'Manager',
        'role': User.ROLE_MANAGER,
        'is_staff': True,
    }
)
manager.set_password('managerpass')
manager.save()

customer, _ = User.objects.get_or_create(
    email='customer@example.com',
    defaults={
        'first_name': 'Customer',
        'role': User.ROLE_CUSTOMER,
    }
)
customer.set_password('customerpass')
customer.save()

# Get JWT token for admin
refresh = RefreshToken.for_user(admin)
access_token = str(refresh.access_token)

# Test endpoints
print("=" * 60)
print("ADMIN API ENDPOINT TESTS")
print("=" * 60)

# 1. Test dashboard overview
print("\n1. Testing /api/v1/admin/dashboard/ (Overview Stats)")
print("-" * 40)
response = client.get('/api/v1/admin/dashboard/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response structure: {list(data.keys())}")
    if 'data' in data:
        print(f"KPIs available: {list(data['data'].keys())}")
else:
    print(f"Error: {response.content}")

# 2. Test users list
print("\n2. Testing /api/v1/admin/users/ (Users List)")
print("-" * 40)
response = client.get('/api/v1/admin/users/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response structure: {list(data.keys())}")
    if 'data' in data and isinstance(data['data'], list):
        print(f"Total users returned: {len(data['data'])}")
        if data['data']:
            print(f"First user: {data['data'][0]}")
else:
    print(f"Error: {response.content}")

# 3. Test user detail endpoint
print(f"\n3. Testing /api/v1/admin/users/{manager.id}/ (User Detail)")
print("-" * 40)
response = client.get(f'/api/v1/admin/users/{manager.id}/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"User data: {json.dumps(data, indent=2)}")
else:
    print(f"Error: {response.content}")

# 4. Test revenue endpoint
print("\n4. Testing /api/v1/admin/revenue/ (Revenue Stats)")
print("-" * 40)
response = client.get('/api/v1/admin/revenue/', HTTP_AUTHORIZATION=f'Bearer {access_token}')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response structure: {list(data.keys())}")
    if 'data' in data:
        print(f"Revenue buckets available: {list(data['data'].keys())}")
else:
    print(f"Error: {response.content}")

# 5. Test permission denial (customer trying to access admin endpoint)
print("\n5. Testing Permission Denial (Customer accessing /api/v1/admin/users/)")
print("-" * 40)
refresh_customer = RefreshToken.for_user(customer)
token_customer = str(refresh_customer.access_token)
response = client.get('/api/v1/admin/users/', HTTP_AUTHORIZATION=f'Bearer {token_customer}')
print(f"Status: {response.status_code}")
if response.status_code == 403:
    print("✓ Customer correctly denied access")
elif response.status_code == 401:
    print("✓ Customer correctly denied access (401 Unauthorized)")
else:
    print(f"✗ Unexpected status: {response.status_code}")
    print(f"Response: {response.content}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
