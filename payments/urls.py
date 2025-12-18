from django.urls import path
from .views import SavePaymentMethodAPIView, ConfirmPaymentAPIView, StripeWebhookAPIView

urlpatterns = [
    # Antes era 'save-method/', ahora le añadimos 'payments/' delante
    path('payments/save-method/', SavePaymentMethodAPIView.as_view(), name='save-payment-method'),

    # Antes era 'confirm/', ahora le añadimos 'payments/' delante
    path('payments/confirm/', ConfirmPaymentAPIView.as_view(), name='confirm-payment'),

    # Webhook
    path('webhooks/stripe/', StripeWebhookAPIView.as_view(), name='webhook-stripe'),
]