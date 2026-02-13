import json
import hmac
import hashlib
import time

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from api.models import Payment, PaymentAudit, Order

User = get_user_model()


def _stripe_signature_for_payload(payload_bytes: bytes, secret: str):
    t = int(time.time())
    signed_payload = b"%d." % t + payload_bytes
    sig = hmac.new(secret.encode('utf-8'), signed_payload, hashlib.sha256).hexdigest()
    return f"t={t},v1={sig}"


def _razorpay_signature_for_payload(payload_bytes: bytes, secret: str):
    return hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()


class PaymentWebhooksTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Ensure webhook secrets exist for tests
        settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        settings.RAZORPAY_WEBHOOK_SECRET = 'rpsec_test'

        self.user = User.objects.create_user(email='buyer@test.local', password='pw', username='buyer')
        self.order = Order.objects.create(user=self.user, total_amount=10.00, shipping_address='x', payment_method='stripe')
        # Payment record that webhook should map to
        self.payment = Payment.objects.create(order=self.order, payment_id='pi_test_123', payment_method='stripe', status='pending', amount=10.00)

    def test_stripe_payment_succeeded_webhook_creates_audit_and_updates_payment(self):
        payload = {
            'id': 'pi_test_123',
            'object': 'payment_intent',
            'status': 'succeeded',
            'amount': 1000,
            'currency': 'usd'
        }
        body = json.dumps({'type': 'payment_intent.succeeded', 'data': {'object': payload}, 'id': 'evt_test'})
        sig = _stripe_signature_for_payload(body.encode('utf-8'), settings.STRIPE_WEBHOOK_SECRET)

        resp = self.client.post(reverse('stripe_webhook'), data=body, content_type='application/json', HTTP_STRIPE_SIGNATURE=sig)
        self.assertEqual(resp.status_code, 200)

        # PaymentAudit created and marked verified
        audits = PaymentAudit.objects.filter(provider='stripe', event_type='payment_intent.succeeded')
        self.assertTrue(audits.exists())
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'completed')

    def test_stripe_webhook_invalid_signature_rejected(self):
        body = json.dumps({'type': 'payment_intent.succeeded', 'data': {'object': {'id': 'pi_test_123'}}, 'id': 'evt_test'})
        resp = self.client.post(reverse('stripe_webhook'), data=body, content_type='application/json', HTTP_STRIPE_SIGNATURE='t=1,v1=invalidsig')
        self.assertEqual(resp.status_code, 400)

    def test_razorpay_payment_captured_webhook_creates_audit_and_updates_payment(self):
        # Create a second payment record which mimics Razorpay id
        rp_payment = Payment.objects.create(order=self.order, payment_id='rp_test_1', payment_method='razorpay', status='pending', amount=10.00)
        payload = {
            'event': 'payment.captured',
            'payload': {'payment': {'entity': {'id': 'rp_test_1', 'status': 'captured', 'amount': 1000}}}
        }
        body = json.dumps(payload)
        sig = _razorpay_signature_for_payload(body.encode('utf-8'), settings.RAZORPAY_WEBHOOK_SECRET)

        resp = self.client.post(reverse('razorpay_webhook'), data=body, content_type='application/json', HTTP_X_RAZORPAY_SIGNATURE=sig)
        self.assertEqual(resp.status_code, 200)

        audits = PaymentAudit.objects.filter(provider='razorpay', event_type='payment.captured')
        self.assertTrue(audits.exists())
        rp_payment.refresh_from_db()
        self.assertEqual(rp_payment.status, 'completed')

    def test_razorpay_invalid_signature_rejected(self):
        body = json.dumps({'event': 'payment.captured', 'payload': {}})
        resp = self.client.post(reverse('razorpay_webhook'), data=body, content_type='application/json', HTTP_X_RAZORPAY_SIGNATURE='invalid')
        self.assertEqual(resp.status_code, 400)