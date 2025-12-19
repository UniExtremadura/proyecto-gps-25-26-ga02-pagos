from django.db import models

# Create your models here.
from django.db import models
import uuid
from orders.models import Order


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice_record')
    invoice_pdf = models.FileField(upload_to='invoices_pdfs/')  # Debe coincidir con tu función
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Factura del pedido {self.order.order_id}"