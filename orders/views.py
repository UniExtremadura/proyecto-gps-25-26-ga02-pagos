from rest_framework import status, generics
from rest_framework.permissions import AllowAny  # <--- IMPORTANTE
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import Http404

from .models import Order, OrderItem
from cart.models import ShoppingCart
from pricing.services import calculate_cart_totals

from .serializers import (
    CreateOrderRequestSerializer,
    OrderAcceptedResponseSerializer,
    OrderResponseSerializer
)


class OrderListCreateAPIView(APIView):
    """
    POST /api/v1/orders
    Crea una nueva orden a partir de los datos del carrito.
    """
    permission_classes = [AllowAny]  # <--- Puerta abierta
    authentication_classes = []  # <--- Sin chequeo de token

    def post(self, request, *args, **kwargs):
        # --- SIMULACIÓN DE USUARIO (Microservicio) ---
        current_user_id = 1
        # ---------------------------------------------

        try:
            # 1. Obtener el carrito activo usando user_id
            cart = get_object_or_404(
                ShoppingCart,
                user_id=current_user_id,  # <--- Usamos el ID numérico
                status=ShoppingCart.CartStatus.ACTIVE
            )
            cart_items = cart.items.all()

            if not cart_items:
                return Response({"error": "El carrito está vacío."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Obtener la región (Hardcodeado por ahora)
            region_code = "ES"

            # 3. Calcular totales (Tu servicio de pricing)
            totals = calculate_cart_totals(cart, region_code)

            # 4. Crear la Orden y los Items (Atomicidad)
            with transaction.atomic():
                order = Order.objects.create(
                    user_id=current_user_id,  # <--- Usamos el ID numérico
                    status=Order.OrderStatus.PENDING,
                    amount=totals['total'],
                    currency="EUR",
                    subtotal=totals['subtotal'],
                    tax_total=totals['tax_amount'],
                    tax_percent=totals['tax_rate_percent'],
                    tax_name=totals['tax_rate_name']
                )

                # 5. Copiar los artículos
                order_items_to_create = []
                for item in cart_items:
                    order_items_to_create.append(
                        OrderItem(
                            order=order,
                            item_type=OrderItem.ItemType.TRACK,
                            product_id=item.product_id,
                            quantity=item.quantity,
                            unit_price=item.price_at_addition
                        )
                    )
                OrderItem.objects.bulk_create(order_items_to_create)

                # 6. Marcar carrito como ORDERED
                cart.status = ShoppingCart.CartStatus.ORDERED
                cart.save()

            # 7. Devolver respuesta
            response_serializer = OrderAcceptedResponseSerializer(order)
            return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

        except Http404:
            return Response({"error": "No se encontró un carrito activo para procesar."},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Es útil imprimir el error en consola para que lo veas tú
            print(f"ERROR EN ORDER CREATE: {e}")
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OrderRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/v1/orders/{order_id}
    """
    permission_classes = [AllowAny]  # <--- Puerta abierta
    authentication_classes = []

    serializer_class = OrderResponseSerializer
    queryset = Order.objects.all()
    lookup_field = 'order_id'

    def get_queryset(self):
        # Filtramos por el ID numérico simulado
        current_user_id = 1
        return Order.objects.filter(user_id=current_user_id)