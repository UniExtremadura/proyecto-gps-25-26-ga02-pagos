from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from proyecto_gps_25_26_ga02_pagos.authentication import JWTAuthenticationSafe
from django.shortcuts import get_object_or_404
from .models import ShoppingCart, CartItem
from .serializers import (
    ShoppingCartSerializer,
    CartItemAddSerializer,
    CartItemDisplaySerializer
)

# HELPER: Obtener o crear carrito (Limpio y robusto)
def get_or_create_cart(user):
    """
    Función helper para Microservicios:
    Busca un carrito basado en un ID numérico (user_id), no en una tabla de usuarios.
    """
    user_id_num = user.id  # Asumimos que 'user' tiene un atributo 'id' numérico

    # 1. Buscamos si existe un carrito activo para este número de usuario
    cart = ShoppingCart.objects.filter(
        user_id=user_id_num,
        status=ShoppingCart.CartStatus.ACTIVE
    ).first()

    # 2. Si no existe, lo creamos asignándole ese número
    if not cart:
        # Opcional: Limpiar carritos viejos si quieres
        ShoppingCart.objects.filter(
            user_id=user_id_num,
            status=ShoppingCart.CartStatus.ORDERED
        ).delete()

        cart = ShoppingCart.objects.create(
            user_id=user_id_num,
            status=ShoppingCart.CartStatus.ACTIVE
        )

    return cart

# VISTA 1: Ver Carrito
class CartRetrieveAPIView(generics.RetrieveAPIView):
    """
    GET /api/v1/cart/
    Muestra el carrito del usuario actual.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ShoppingCartSerializer

    def get_object(self):
        return get_or_create_cart(self.request.user)


# VISTA 2: Añadir Item
class CartItemAddAPIView(generics.CreateAPIView):
    """
    POST /api/v1/cart/items/
    """
    # 1. SEGURIDAD: Usamos la clase segura que importamos arriba
    # 2. PERMISOS: Solo gente logueada
    permission_classes = [IsAuthenticated]

    serializer_class = CartItemAddSerializer

    def perform_create(self, serializer):
        # Al usar JWTAuthenticationSafe, request.user ya es el usuario correcto
        cart = get_or_create_cart(self.request.user)

        product_id = serializer.validated_data.get('product_id')
        quantity = serializer.validated_data.get('quantity', 1)
        price = serializer.validated_data.get('price_at_addition')

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
            item.quantity += quantity
            if price:
                item.price_at_addition = price
            item.save()
            serializer.instance = item
        except CartItem.DoesNotExist:
            serializer.save(cart=cart)

    def get_serializer(self, *args, **kwargs):
        if 'instance' in kwargs:
            kwargs['context'] = self.get_serializer_context()
            return CartItemDisplaySerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)


# VISTA 3: Borrar Item
class CartItemDestroyAPIView(generics.DestroyAPIView):
    """
    DELETE /api/v1/cart/items/{id}/
    Borra un ítem del carrito.
    """
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        # Solo permitimos borrar ítems del usuario actual
        # Primero aseguramos que el carrito existe/pertenece al usuario
        cart = get_or_create_cart(self.request.user)
        return CartItem.objects.filter(cart=cart)