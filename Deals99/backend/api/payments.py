"""
Payment processing module for Deals99
Handles Stripe and Razorpay payment integrations
"""

import logging
import stripe
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from rest_framework import status

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None


# Small helper to persist payment webhook/audit events
def _log_payment_audit(provider: str, event_type: str, payload: dict, verified: bool = False):
    try:
        from .models import PaymentAudit, Payment
        payment = None
        # attempt to associate with a Payment record by common keys
        payment_id = payload.get('id') or payload.get('payment_intent') or payload.get('payment_id')
        if payment_id:
            payment = Payment.objects.filter(payment_id=payment_id).first()
        PaymentAudit.objects.create(
            payment=payment,
            provider=provider,
            event_type=event_type,
            payload=payload,
            verified=verified,
        )
    except Exception:
        logger.exception('Failed to record payment audit')


class PaymentProcessor:
    """Main payment processing class"""

    @staticmethod
    def create_payment_intent(order, payment_method='stripe'):
        """Create a payment intent for an order"""
        try:
            if payment_method == 'stripe':
                return StripePaymentProcessor.create_payment_intent(order)
            elif payment_method == 'razorpay':
                return RazorpayPaymentProcessor.create_payment_intent(order)
            else:
                logger.error(f"Unknown payment method: {payment_method}")
                return {'success': False, 'error': 'Unknown payment method'}
        except Exception as e:
            logger.error(f"Error creating payment intent for order {order.order_number}: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def verify_payment(payment_id, payment_method='stripe'):
        """Verify a payment"""
        try:
            if payment_method == 'stripe':
                return StripePaymentProcessor.verify_payment(payment_id)
            elif payment_method == 'razorpay':
                return RazorpayPaymentProcessor.verify_payment(payment_id)
            else:
                return {'success': False, 'error': 'Unknown payment method'}
        except Exception as e:
            logger.error(f"Error verifying payment {payment_id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def refund_payment(payment_id, amount=None, payment_method='stripe'):
        """Refund a payment"""
        try:
            if payment_method == 'stripe':
                return StripePaymentProcessor.refund_payment(payment_id, amount)
            elif payment_method == 'razorpay':
                return RazorpayPaymentProcessor.refund_payment(payment_id, amount)
            else:
                return {'success': False, 'error': 'Unknown payment method'}
        except Exception as e:
            logger.error(f"Error refunding payment {payment_id}: {str(e)}", exc_info=True)
            return {'success': False, 'error': str(e)}


class StripePaymentProcessor:
    """Stripe payment processor implementation"""

    @staticmethod
    def create_payment_intent(order):
        """Create a Stripe payment intent"""
        try:
            if not stripe.api_key:
                logger.error("Stripe API key not configured")
                return {'success': False, 'error': 'Payment system not configured'}

            # Convert amount to cents (Stripe uses cents for USD)
            amount_cents = int(float(order.total_amount) * 100)

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                metadata={
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'customer_email': order.user.email,
                },
                description=f'Order {order.order_number} - {order.user.username}'
            )

            logger.info(f"Stripe payment intent created for order {order.order_number}: {intent.id}")

            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': float(order.total_amount),
                'currency': 'usd'
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Stripe payment processing failed'}
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Payment processing error'}

    @staticmethod
    def verify_payment(payment_intent_id):
        """Verify a Stripe payment"""
        try:
            if not stripe.api_key:
                return {'success': False, 'error': 'Payment system not configured'}

            intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if intent.status == 'succeeded':
                logger.info(f"Stripe payment verified: {payment_intent_id}")
                _log_payment_audit('stripe', 'payment_intent.succeeded', intent.to_dict(), verified=True)
                return {
                    'success': True,
                    'payment_id': intent.id,
                    'status': 'completed',
                    'amount': Decimal(intent.amount) / 100,
                }
            elif intent.status in ['processing', 'requires_action']:
                _log_payment_audit('stripe', f'payment_intent.{intent.status}', intent.to_dict(), verified=True)
                return {
                    'success': True,
                    'payment_id': intent.id,
                    'status': 'pending',
                }
            else:
                logger.warning(f"Stripe payment failed: {payment_intent_id} - Status: {intent.status}")
                _log_payment_audit('stripe', f'payment_intent.{intent.status}', intent.to_dict(), verified=False)
                return {
                    'success': False,
                    'payment_id': intent.id,
                    'status': 'failed',
                    'error': f'Payment {intent.status}'
                }

        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe payment ID: {payment_intent_id}")
            return {'success': False, 'error': 'Invalid payment ID'}
        except Exception as e:
            logger.error(f"Error verifying Stripe payment: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Payment verification failed'}

    @staticmethod
    def refund_payment(payment_intent_id, amount=None):
        """Refund a Stripe payment"""
        try:
            if not stripe.api_key:
                return {'success': False, 'error': 'Payment system not configured'}

            # Get the charge ID from the payment intent
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not intent.charges.data:
                return {'success': False, 'error': 'No charge found for this payment'}

            charge = intent.charges.data[0]

            # Create refund
            refund_params = {'charge': charge.id}
            if amount:
                refund_params['amount'] = int(float(amount) * 100)

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Stripe refund created: {refund.id} for payment {payment_intent_id}")

            return {
                'success': True,
                'refund_id': refund.id,
                'amount': Decimal(refund.amount) / 100,
                'status': refund.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Refund failed'}
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Refund processing error'}


class RazorpayPaymentProcessor:
    """Razorpay payment processor implementation"""

    @staticmethod
    def create_payment_intent(order):
        """Create a Razorpay order"""
        try:
            import razorpay
            
            key_id = settings.RAZORPAY_KEY_ID if hasattr(settings, 'RAZORPAY_KEY_ID') else None
            key_secret = settings.RAZORPAY_KEY_SECRET if hasattr(settings, 'RAZORPAY_KEY_SECRET') else None

            if not key_id or not key_secret:
                logger.error("Razorpay credentials not configured")
                return {'success': False, 'error': 'Payment system not configured'}

            client = razorpay.Client(auth=(key_id, key_secret))

            # Razorpay expects amount in paise (cents)
            amount_paise = int(float(order.total_amount) * 100)

            razorpay_order = client.order.create(
                amount=amount_paise,
                currency='INR',
                payment_capture=1,
                notes={
                    'order_id': order.id,
                    'order_number': order.order_number,
                    'customer_email': order.user.email,
                }
            )

            logger.info(f"Razorpay order created for order {order.order_number}: {razorpay_order['id']}")

            return {
                'success': True,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': key_id,
                'amount': float(order.total_amount),
                'currency': 'INR'
            }

        except Exception as e:
            logger.error(f"Razorpay error creating order: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Razorpay payment processing failed'}

    @staticmethod
    def verify_payment(razorpay_payment_id):
        """Verify a Razorpay payment"""
        try:
            import razorpay
            
            key_id = settings.RAZORPAY_KEY_ID if hasattr(settings, 'RAZORPAY_KEY_ID') else None
            key_secret = settings.RAZORPAY_KEY_SECRET if hasattr(settings, 'RAZORPAY_KEY_SECRET') else None

            if not key_id or not key_secret:
                return {'success': False, 'error': 'Payment system not configured'}

            client = razorpay.Client(auth=(key_id, key_secret))
            payment = client.payment.fetch(razorpay_payment_id)

            if payment['status'] == 'captured':
                logger.info(f"Razorpay payment verified: {razorpay_payment_id}")
                return {
                    'success': True,
                    'payment_id': payment['id'],
                    'status': 'completed',
                    'amount': Decimal(payment['amount']) / 100,
                }
            else:
                return {
                    'success': False,
                    'payment_id': payment['id'],
                    'status': payment['status'],
                    'error': f'Payment {payment["status"]}'
                }

        except Exception as e:
            logger.error(f"Error verifying Razorpay payment: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Payment verification failed'}

    @staticmethod
    def refund_payment(razorpay_payment_id, amount=None):
        """Refund a Razorpay payment"""
        try:
            import razorpay
            
            key_id = settings.RAZORPAY_KEY_ID if hasattr(settings, 'RAZORPAY_KEY_ID') else None
            key_secret = settings.RAZORPAY_KEY_SECRET if hasattr(settings, 'RAZORPAY_KEY_SECRET') else None

            if not key_id or not key_secret:
                return {'success': False, 'error': 'Payment system not configured'}

            client = razorpay.Client(auth=(key_id, key_secret))

            refund_params = {}
            if amount:
                refund_params['amount'] = int(float(amount) * 100)

            refund = client.payment.refund(razorpay_payment_id, refund_params)

            logger.info(f"Razorpay refund created: {refund['id']} for payment {razorpay_payment_id}")

            return {
                'success': True,
                'refund_id': refund['id'],
                'amount': Decimal(refund['amount']) / 100,
                'status': refund['status']
            }

        except Exception as e:
            logger.error(f"Error processing Razorpay refund: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Refund processing error'}
