from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

# NOTA: Ya no importamos 'User' ni 'get_user_model' porque somos un microservicio independiente.

from .models import ShoppingCart, CartItem
from .serializers import (
    ShoppingCartSerializer,
    CartItemAddSerializer,
    CartItemDisplaySerializer
)


def get_or_create_cart(user_id_number):
    """
    Función helper para Microservicios:
    Busca un carrito basado en un ID numérico (user_id), no en una tabla de usuarios.
    """
    # 1. Buscamos si existe un carrito activo para este número de usuario
    cart = ShoppingCart.objects.filter(
        user_id=user_id_number,
        status=ShoppingCart.CartStatus.ACTIVE
    ).first()

    # 2. Si no existe, lo creamos asignándole ese número
    if not cart:
        # Opcional: Limpiar carritos viejos si quieres
        ShoppingCart.objects.filter(
            user_id=user_id_number,
            status=ShoppingCart.CartStatus.ORDERED
        ).delete()

        cart = ShoppingCart.objects.create(
            user_id=user_id_number,
            status=ShoppingCart.CartStatus.ACTIVE
        )

    return cart


class CartRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/v1/cart/
    Muestra el carrito del usuario actual.
    """
    permission_classes = [AllowAny]
    serializer_class = ShoppingCartSerializer

    def get_object(self):
        # SIMULACIÓN: Asumimos que somos el usuario ID 1
        current_user_id = 1
        return get_or_create_cart(current_user_id)


class CartItemAddAPIView(generics.CreateAPIView):
    """
    POST /api/v1/cart/items/
    Añade ítems al carrito.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Sin seguridad por ahora

    serializer_class = CartItemAddSerializer

    def perform_create(self, serializer):
        # --- LÓGICA DE MICROSERVICIO ---
        # Aquí fingimos ser el Usuario con ID 1.
        # Al no usar request.user, no necesitamos la tabla auth_user.
        current_user_id = 1
        # -------------------------------

        cart = get_or_create_cart(current_user_id)

        product_id = serializer.validated_data.get('product_id')
        quantity = serializer.validated_data.get('quantity', 1)
        price = serializer.validated_data.get('price_at_addition')

        try:
            # Si el producto ya está, sumamos cantidad
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.quantity += quantity
            if price:
                item.price_at_addition = price
            item.save()
            serializer.instance = item
        except CartItem.DoesNotExist:
            # Si es nuevo, lo creamos
            serializer.save(cart=cart)

    def get_serializer(self, *args, **kwargs):
        # Usamos el serializer de visualización para la respuesta
        if 'instance' in kwargs:
            kwargs['context'] = self.get_serializer_context()
            return CartItemDisplaySerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)


class CartItemDestroyAPIView(generics.DestroyAPIView):
    """
    DELETE /api/v1/cart/items/{id}/
    Borra un ítem del carrito.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    lookup_field = 'pk'

    def get_queryset(self):
        # Solo permitimos borrar ítems del usuario 1
        current_user_id = 1
        cart = get_or_create_cart(current_user_id)
        return CartItem.objects.filter(cart=cart)