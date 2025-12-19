from django.urls import path
from .views import download_invoice_on_demand

urlpatterns = [
    # URL: /api/v1/invoices/download/<uuid>/
    path('download/<uuid:order_id>/', download_invoice_on_demand, name='invoice-download'),
]