from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from api.models import Cart, Order, OrderItem, Product


class EmptyCartError(Exception):
    """Raised when attempting to create an order from an empty cart."""


@dataclass
class OrderCreationResult:
    order: Order
    total_amount: Decimal


@transaction.atomic
def create_order_from_cart(user, shipping_address: str, payment_method: str = 'cod') -> OrderCreationResult:
    """
    Create an order (and order items) for the given user based on current cart contents.

    - Locks cart rows and related product rows to prevent concurrent oversells.
    - Validates available stock and records StockTransaction entries.
    - Uses a single atomic transaction to ensure consistency.
    """
    cart_items = (
        Cart.objects.select_related('product')
        .select_for_update()
        .filter(user=user)
    )

    if not cart_items.exists():
        raise EmptyCartError("Cart is empty")

    # Lock the product rows referenced by the cart to avoid race conditions
    product_ids = [ci.product_id for ci in cart_items]
    products_locked = list(Product.objects.select_for_update().filter(pk__in=product_ids))
    products_map = {p.id: p for p in products_locked}

    # Validate stock levels before creating the order
    for ci in cart_items:
        product = products_map.get(ci.product_id)
        if product is None:
            raise EmptyCartError(f"Product not found: {ci.product_id}")
        if product.stock < ci.quantity:
            raise ValueError(f"Insufficient stock for product {product.name}")

    total_amount = sum((item.total_price for item in cart_items), Decimal('0.00'))

    order = Order.objects.create(
        user=user,
        total_amount=total_amount,
        shipping_address=shipping_address or '',
        payment_method=payment_method or 'cod',
    )

    # Create order items and decrement stock in a safe, atomic way
    order_items = []
    stock_txns = []
    for cart_item in cart_items:
        prod = products_map[cart_item.product_id]
        order_items.append(
            OrderItem(
                order=order,
                product=prod,
                quantity=cart_item.quantity,
                price=prod.price,
            )
        )
        # Apply stock change
        prod.stock = prod.stock - cart_item.quantity
        prod.save(update_fields=['stock'])

        # Record stock transaction
        from api.models import StockTransaction
        stock_txns.append(StockTransaction(
            product=prod,
            change=-int(cart_item.quantity),
            reason='order',
            reference_id=order.order_number
        ))

    OrderItem.objects.bulk_create(order_items)
    StockTransaction.objects.bulk_create(stock_txns)

    # Clear cart once order and items are created
    cart_items.delete()

    return OrderCreationResult(order=order, total_amount=total_amount)


def update_order_status(order: Order, new_status: str) -> Order:
    """
    Centralised helper to update an order status with validation.
    Does not handle permissions – those should be enforced at the view layer.
    """
    valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
    if new_status not in valid_statuses:
        raise ValueError("Invalid order status.")

    order.status = new_status
    order.save(update_fields=['status', 'updated_at'])
    return order

