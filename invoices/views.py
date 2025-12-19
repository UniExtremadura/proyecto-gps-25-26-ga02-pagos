# invoices/views.py
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from proyecto_gps_25_26_ga02_pagos.authentication import JWTAuthenticationSafe
from orders.models import Order
from payments.services import generate_invoice_pdf_for_order


@api_view(['GET'])
@authentication_classes([JWTAuthenticationSafe])
@permission_classes([IsAuthenticated])
def download_invoice_on_demand(request, order_id):
    # 1. Validar pedido y usuario
    order = get_object_or_404(Order, order_id=order_id, user_id=request.user.id)

    # 2. Llamar a tu función (que genera y guarda en BD si no existe)
    invoice_obj = generate_invoice_pdf_for_order(order)

    # 3. Servir el archivo guardado en el campo invoice_pdf
    return FileResponse(
        invoice_obj.invoice_pdf.open('rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename=f"Factura_{order.order_id.hex[:8]}.pdf"
    )