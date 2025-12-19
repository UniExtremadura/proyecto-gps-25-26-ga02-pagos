from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny  # <--- Importar AllowAny
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
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # --- CORRECCIÓN 1: Usar datos REALES del usuario logueado ---
        user = request.user
        current_user_id = user.id
        # Intentamos sacar el email, si no tiene, inventamos uno consistente
        current_user_email = getattr(user, 'email', f'user_{current_user_id}@novatune.local')
        # ------------------------------------------------------------

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
                    name=f"Usuario {current_user_id}",
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
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get('order_id')
        pm_id = request.data.get('payment_method_id')

        customer_id = request.data.get('customer_id')

        if not order_id or not pm_id:
            return Response(
                {"error": "Faltan datos (order_id o payment_method_id)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Extraemos el ID numérico del usuario
        user = request.user

        try:
            order = Order.objects.get(
                id=order_id,
                user_id=user.id,
                status=Order.OrderStatus.PENDING
            )
        except Order.DoesNotExist:
            return Response(
                {"error": "Orden no encontrada o ya pagada"},
                status=status.HTTP_404_NOT_FOUND
            )
        # 2. Si no viene customer_id, intentamos buscarlo en Stripe por email
        if not customer_id:
            search = stripe.Customer.search(
                query=f"email:'{getattr(user, 'email', f'user_{user.id}@novatune.local')}'",
                limit=1
            )
            if search.data:
                customer_id = search.data[0].id

        try:
            # 3. Crear PaymentIntent CON customer
            intent_data = {
                "amount": int(order.amount * 100),
                "currency": order.currency.lower(),
                "payment_method": pm_id,
                "confirm": True,
                "return_url": "http://localhost:5173/checkout/result",
                "metadata": {'order_id': order.id}
            }

            if customer_id:
                intent_data["customer"] = customer_id

            intent = stripe.PaymentIntent.create(**intent_data)

            return Response({
                'client_secret': intent.client_secret,
                'status': intent.status
            })


        except stripe.StripeError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPIView(APIView):
    # --- CORRECCIÓN 3: El Webhook debe ser público ---
    permission_classes = [AllowAny]

    # -------------------------------------------------

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return Response(status=400)
        except stripe.error.SignatureVerificationError as e:
            return Response(status=400)

        # Aquí procesarías el evento (payment_intent.succeeded)
        # Para ahora, devolvemos 200 OK para que Stripe sepa que lo recibimos
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            print(f"💰 WEBHOOK: Pago recibido! ID: {payment_intent['id']}")
            # Aquí podrías buscar la Orden por metadatos y marcarla como pagada
            # order_id = payment_intent['metadata'].get('order_id')
            # ... lógica para actualizar DB ...

        return Response(status=status.HTTP_200_OK)