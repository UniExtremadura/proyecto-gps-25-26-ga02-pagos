import uuid
from django.db import models
from typing import Any


# Eliminamos la dependencia de settings y auth_user_model

class Order(models.Model):
    """
    Representa un pedido completo.
    """

    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        PAID = 'PAID', 'Pagado'
        FAILED = 'FAILED', 'Fallido'
        REFUNDED = 'REFUNDED', 'Reembolsado'

    order_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user_id = models.PositiveIntegerField(help_text="ID del usuario (Microservicio Usuarios)", default=1)

    status = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )

    # ----- Detalles de pago -----
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='EUR')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax_name = models.CharField(max_length=100, default="N/A")
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.order_id} - UserID: {self.user_id} - Estado: {self.status}"


class OrderItem(models.Model):
    """
    Los articulos dentro de un pedido
    """

    class ItemType(models.TextChoices):
        ALBUM = 'ALBUM', 'Álbum'
        TRACK = 'TRACK', 'Canción'
        SUB = 'SUB', 'Suscripción'

    item_type = models.CharField(
        max_length=10,
        choices=ItemType.choices,
        default=ItemType.TRACK
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='lines')

    product_id = models.IntegerField()
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Unidad del producto')

    @property
    def line_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"Item {self.product_id} (x{self.quantity}) en Pedido {self.order.order_id}"


class Invoice(models.Model):
    """
    Representa la factura generada DESPUÉS de un pago exitoso.
    """
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='invoice')
    invoice_pdf = models.FileField(upload_to='invoices/%Y/%m/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Factura para Pedido {self.order.order_id}"