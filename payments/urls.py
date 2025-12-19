from django.urls import path
from .views import SavePaymentMethodAPIView, ConfirmPaymentAPIView, StripeWebhookAPIView

urlpatterns = [
    # ALERTA: Aquí SÍ hace falta poner 'payments/' porque tu urls.py principal no lo pone.

    # Ruta final: /api/v1/payments/save-method/
    path('payments/save-method/', SavePaymentMethodAPIView.as_view(), name='save-payment-method'),

    # Ruta final: /api/v1/payments/confirm/
    path('payments/confirm/', ConfirmPaymentAPIView.as_view(), name='confirm-payment'),

    # Ruta final: /api/v1/webhooks/stripe/ (o payments/webhooks/stripe si prefieres)
    path('webhooks/stripe/', StripeWebhookAPIView.as_view(), name='webhook-stripe'),
]