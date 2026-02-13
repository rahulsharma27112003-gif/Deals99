from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

from .notifications import EmailNotificationService
from .models import Order, Product, Refund

logger = logging.getLogger(__name__)


@shared_task(bind=True, acks_late=True)
def send_order_confirmation_task(self, order_id):
    try:
        order = Order.objects.select_related('user').get(pk=order_id)
    except ObjectDoesNotExist:
        logger.error('Order not found for confirmation task: %s', order_id)
        return False
    return EmailNotificationService.send_order_confirmation(order)


@shared_task(bind=True, acks_late=True)
def send_order_status_update_task(self, order_id):
    try:
        order = Order.objects.select_related('user').get(pk=order_id)
    except ObjectDoesNotExist:
        logger.error('Order not found for status task: %s', order_id)
        return False
    return EmailNotificationService.send_order_status_update(order)


@shared_task(bind=True, acks_late=True)
def send_low_stock_alert_task(self, product_id):
    try:
        product = Product.objects.get(pk=product_id)
    except ObjectDoesNotExist:
        logger.error('Product not found for low stock alert: %s', product_id)
        return False
    return EmailNotificationService.send_low_stock_alert(product)


@shared_task(bind=True, acks_late=True)
def process_refund_task(self, refund_id):
    try:
        refund = Refund.objects.get(pk=refund_id)
    except ObjectDoesNotExist:
        logger.error('Refund not found for processing: %s', refund_id)
        return False
    # Placeholder: integrate with payment provider here; mark completed for now
    refund.status = 'processing'
    refund.save()
    # Simulate external refund processing and update
    # (real implementation should call payment API + webhook)
    refund.status = 'completed'
    refund.completed_at = refund.updated_at
    refund.save()
    return True
