from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe
import logging
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class SavePaymentMethodAPIView(APIView):
    """
    Recibe el ID del PaymentMethod desde el frontend (Stripe Elements)
    y lo asocia a un Customer en Stripe.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        # 1. Simulación de usuario
        current_user_id = 1
        current_user_email = "usuario_demo@test.com"

        # 2. Datos del frontend
        pm_id = request.data.get('payment_method_id')

        if not pm_id:
            return Response({"error": "Falta el payment_method_id"}, status=400)

        try:
            # 3. Buscar o Crear Customer EN STRIPE
            search = stripe.Customer.search(
                query=f"email:'{current_user_email}'",
                limit=1
            )

            if search.data:
                customer = search.data[0]
            else:
                customer = stripe.Customer.create(
                    email=current_user_email,
                    name=f"Usuario Demo {current_user_id}",
                    metadata={'user_id': str(current_user_id)}
                )

            # 4. Adjuntar el método de pago al cliente
            stripe.PaymentMethod.attach(pm_id, customer=customer.id)

            # 5. Marcarlo como por defecto
            stripe.Customer.modify(
                customer.id,
                invoice_settings={'default_payment_method': pm_id}
            )

            return Response({
                "payment_method_id": pm_id,
                "customer_id": customer.id,
                "message": "Método guardado correctamente"
            }, status=200)

        except stripe.StripeError as e:
            return Response({"error": str(e)}, status=400)


class ConfirmPaymentAPIView(APIView):
    """
    Recibe order_id y payment_method_id para ejecutar el cobro final.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')
        pm_id = request.data.get('payment_method_id')
        current_user_id = 1

        # Nota: Usamos filter().first() para evitar errores 404 bruscos
        order = Order.objects.filter(
            order_id=order_id,
            user_id=current_user_id,
            status=Order.OrderStatus.PENDING
        ).first()

        if not order:
            return Response({"error": "Orden no encontrada o ya pagada"}, status=404)

        try:
            amount_cents = int(order.amount * 100)
            pm_obj = stripe.PaymentMethod.retrieve(pm_id)
            customer_id = pm_obj.customer

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="eur",
                customer=customer_id,
                payment_method=pm_id,
                confirm=True,
                off_session=True,
                return_url="http://localhost:5173/checkout/success",
                metadata={"order_id": str(order.order_id)}
            )

            if intent.status == 'succeeded':
                order.status = Order.OrderStatus.PAID
                order.save()

            return Response({
                "status": intent.status,
                "client_secret": intent.client_secret
            }, status=200)

        except stripe.CardError as e:
            return Response({"error": e.user_message}, status=400)
        except stripe.StripeError as e:
            return Response({"error": str(e)}, status=500)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=500)


# --- ESTA ES LA CLASE QUE FALTABA ---
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        # Devolvemos un OK simple para que Stripe no se queje
        return Response(status=status.HTTP_200_OK)