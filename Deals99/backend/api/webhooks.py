import hmac
import hashlib
import time
import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status

from .models import Payment, PaymentAudit, Refund

logger = logging.getLogger(__name__)


def _verify_stripe_signature(payload_bytes: bytes, sig_header: str, secret: str, tolerance: int = 300) -> bool:
    """Lightweight Stripe-style signature verification used when stripe.Webhook is not available.

    Expects header format: "t=<timestamp>,v1=<signature>" where signature is hex HMAC-SHA256
    over the string "{timestamp}.{payload}" using the webhook secret.
    """
    if not sig_header or not secret:
        return False

    try:
        parts = dict(pair.split('=') for pair in sig_header.split(',') if '=' in pair)
        timestamp = int(parts.get('t'))
        signature = parts.get('v1')
    except Exception:
        return False

    # Check timestamp tolerance to prevent replay attacks
    if abs(time.time() - timestamp) > tolerance:
        return False

    signed_payload = b"%d." % timestamp + payload_bytes
    expected_sig = hmac.new(secret.encode('utf-8'), signed_payload, hashlib.sha256).hexdigest()
    # Use hmac.compare_digest for constant-time comparison
    return hmac.compare_digest(expected_sig, signature)


def _verify_razorpay_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """Razorpay webhook signature verification using HMAC SHA256 over the payload body."""
    if not signature or not secret:
        return False
    expected = hmac.new(secret.encode('utf-8'), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body or b''
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

        verified = False
        # Prefer official library verification if available
        try:
            import stripe
            if secret and hasattr(stripe, 'Webhook'):
                try:
                    event = stripe.Webhook.construct_event(payload, sig_header, secret)
                    verified = True
                except Exception:
                    verified = _verify_stripe_signature(payload, sig_header, secret)
            else:
                verified = _verify_stripe_signature(payload, sig_header, secret)
        except Exception:
            verified = _verify_stripe_signature(payload, sig_header, secret)

        # Record audit entry regardless of verification result
        try:
            body = json.loads(payload.decode('utf-8') or '{}')
        except Exception:
            body = {'raw': payload.decode('utf-8', errors='ignore')}

        PaymentAudit.objects.create(
            provider='stripe', event_type=body.get('type', 'unknown'), payload=body, verified=verified
        )

        if not verified:
            logger.warning('Stripe webhook signature verification failed')
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        # Handle a few important event types
        event_type = body.get('type')
        data = body.get('data', {}).get('object', {})

        # Payment succeeded
        if event_type in ('payment_intent.succeeded', 'charge.succeeded'):
            payment_intent_id = data.get('id') or data.get('payment_intent')
            # Try to associate with internal Payment record
            payment = Payment.objects.filter(payment_id=payment_intent_id).first()
            if payment:
                payment.status = 'completed'
                payment.completed_at = payment.updated_at
                payment.save(update_fields=['status', 'completed_at', 'updated_at'])
        # Refund created
        if event_type and event_type.startswith('charge.refund') or event_type == 'charge.refunded':
            # Create a Refund record placeholder for auditing; real refund logic handled elsewhere
            charge = data
            payment_id = charge.get('payment_intent') or charge.get('id')
            payment = Payment.objects.filter(payment_id=payment_id).first()
            if payment:
                Refund.objects.create(payment=payment, refund_id=body.get('id', ''), amount=body.get('amount', 0), status='processing')

        return JsonResponse({'received': True})


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body or b''
        signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
        secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)

        verified = False
        # Prefer razorpay util if available
        try:
            import razorpay
            util = getattr(razorpay, 'Utility', None)
            if util and secret:
                try:
                    util.verify_webhook_signature(payload.decode('utf-8'), signature, secret)
                    verified = True
                except Exception:
                    verified = _verify_razorpay_signature(payload, signature, secret)
            else:
                verified = _verify_razorpay_signature(payload, signature, secret)
        except Exception:
            verified = _verify_razorpay_signature(payload, signature, secret)

        # Parse body and create audit
        try:
            body = json.loads(payload.decode('utf-8') or '{}')
        except Exception:
            body = {'raw': payload.decode('utf-8', errors='ignore')}

        PaymentAudit.objects.create(provider='razorpay', event_type=body.get('event', 'unknown'), payload=body, verified=verified)

        if not verified:
            logger.warning('Razorpay webhook signature verification failed')
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        event = body.get('event')
        payload_obj = body.get('payload', {})

        # Example: payment captured
        if event == 'payment.captured':
            payment_data = payload_obj.get('payment', {}).get('entity', {})
            razorpay_payment_id = payment_data.get('id')
            # Associate with Payment
            payment = Payment.objects.filter(payment_id=razorpay_payment_id).first()
            if payment:
                payment.status = 'completed'
                payment.completed_at = payment.updated_at
                payment.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Refund events
        if event and event.startswith('refund.'):
            refund_entity = payload_obj.get('refund', {}).get('entity', {})
            payment_id = refund_entity.get('payment_id')
            payment = Payment.objects.filter(payment_id=payment_id).first()
            if payment:
                Refund.objects.create(payment=payment, refund_id=refund_entity.get('id', ''), amount=refund_entity.get('amount', 0), status='processing')

        return JsonResponse({'status': 'ok'})