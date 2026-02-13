"""
Email notification system for Deals99
Handles all email communications for orders, confirmations, and alerts
"""

import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""

    @staticmethod
    def send_order_confirmation(order):
        """Send order confirmation email to customer"""
        try:
            subject = f"Order Confirmation - {order.order_number}"
            
            context = {
                'order': order,
                'customer_name': order.user.get_full_name() or order.user.username,
                'order_number': order.order_number,
                'order_date': order.created_at.strftime('%B %d, %Y'),
                'total_amount': order.total_amount,
                'items': order.items.all(),
                'shipping_address': order.shipping_address,
                'payment_method': order.get_payment_method_display(),
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('emails/order_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Order confirmation email sent for order {order.order_number} to {order.user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation for {order.order_number}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_order_status_update(order):
        """Send order status update email"""
        try:
            subject = f"Order Update - {order.order_number} ({order.get_status_display()})"
            
            context = {
                'order': order,
                'customer_name': order.user.get_full_name() or order.user.username,
                'order_number': order.order_number,
                'status': order.get_status_display(),
                'status_message': EmailNotificationService._get_status_message(order.status),
                'order_url': f"{settings.SITE_URL}/order.html?id={order.id}",
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('emails/order_status_update.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Order status update email sent for {order.order_number} to {order.user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order status update for {order.order_number}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_registration_confirmation(user):
        """Send registration confirmation email (informational).

        For email verification we have a separate `send_verification_email` helper that
        includes a one-time token.
        """
        try:
            subject = "Welcome to Deals99!"
            
            context = {
                'username': user.get_full_name() or getattr(user, 'email', ''),
                'email': user.email,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('emails/registration_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Registration confirmation email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send registration confirmation for {user.email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_verification_email(user, token):
        """Send an email verification link containing a signed token."""
        try:
            subject = "Verify your email for Deals99"
            verify_url = f"{settings.SITE_URL}/verify-email?token={token}"
            context = {
                'username': user.get_full_name() or getattr(user, 'email', ''),
                'verify_url': verify_url,
                'site_url': settings.SITE_URL,
            }
            html_message = render_to_string('emails/registration_confirmation.html', context)
            plain_message = strip_tags(html_message)
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            logger.info(f"Verification email sent to {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email for {user.email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_password_reset(user, reset_token):
        """Send password reset email"""
        try:
            subject = "Reset Your Deals99 Password"
            
            reset_url = f"{settings.SITE_URL}/reset-password.html?token={reset_token}"
            
            context = {
                'username': user.get_full_name() or user.username,
                'reset_url': reset_url,
                'expiry_hours': 24,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('emails/password_reset.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email for {user.email}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_low_stock_alert(product):
        """Send low stock alert to admins"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
            if not admin_emails:
                return False
            
            subject = f"Low Stock Alert - {product.name}"
            
            context = {
                'product': product,
                'current_stock': product.stock,
                'low_stock_threshold': 10,
                'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
            }
            
            html_message = render_to_string('emails/low_stock_alert.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=list(admin_emails)
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.warning(f"Low stock alert sent for product {product.name} (Stock: {product.stock})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send low stock alert for {product.name}: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def _get_status_message(status):
        """Get user-friendly status message"""
        messages = {
            'pending': 'Your order has been received and is being processed.',
            'processing': 'Your order is being prepared for shipment.',
            'shipped': 'Your order has been shipped! Check your tracking details.',
            'delivered': 'Your order has been delivered. Thank you for shopping!',
            'cancelled': 'Your order has been cancelled.',
        }
        return messages.get(status, 'Your order status has been updated.')


class NotificationTrigger:
    """Triggers notifications at appropriate points in the order lifecycle.

    Tasks are dispatched to Celery when available; falls back to synchronous sending
    to preserve behavior in development/test environments.
    """

    @staticmethod
    def on_order_created(order):
        logger.info(f"Order creation notification trigger for {order.order_number}")
        try:
            from .tasks import send_order_confirmation_task
            send_order_confirmation_task.delay(order.id)
        except Exception:
            EmailNotificationService.send_order_confirmation(order)

    @staticmethod
    def on_order_status_changed(order):
        logger.info(f"Order status change notification trigger for {order.order_number}")
        try:
            from .tasks import send_order_status_update_task
            send_order_status_update_task.delay(order.id)
        except Exception:
            EmailNotificationService.send_order_status_update(order)

    @staticmethod
    def on_user_registered(user):
        logger.info(f"User registration notification trigger for {user.email}")
        # Keep registration confirmation synchronous (lightweight), verification uses separate flow
        EmailNotificationService.send_registration_confirmation(user)

    @staticmethod
    def on_low_stock(product):
        logger.warning(f"Low stock notification trigger for {product.name}")
        try:
            from .tasks import send_low_stock_alert_task
            send_low_stock_alert_task.delay(product.id)
        except Exception:
            EmailNotificationService.send_low_stock_alert(product)
