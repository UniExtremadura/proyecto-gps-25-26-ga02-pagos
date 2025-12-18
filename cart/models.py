from django.db import models
from decimal import Decimal
# Borramos 'from django.conf import settings' porque ya no lo necesitamos

class ShoppingCart(models.Model):
    """
    Modelo que representa el carrito de un usuario.
    """
    class CartStatus(models.TextChoices):
        ACTIVE = 'active', 'Activo'
        ORDERED = 'ordered', 'Ordenado'

    status = models.CharField(
        max_length=10,
        choices=CartStatus.choices,
        default=CartStatus.ACTIVE
    )

    # --- CAMBIO IMPORTANTE: MICROSERVICIO PURO ---
    # Antes: user = models.OneToOneField(settings.AUTH_USER_MODEL...)
    # Ahora: Guardamos solo el ID numérico que viene del microservicio de Usuarios.
    # Quitamos unique=True estricto para permitir que en el futuro guardes carritos viejos (ORDERED).
    user_id = models.PositiveIntegerField(
        help_text="ID del usuario (referencia al microservicio de Usuarios)",
        db_index=True,
        default=1 # Valor por defecto temporal para evitar errores en migraciones
    )
    # ---------------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Ya no podemos usar self.user.username porque no tenemos el objeto user
        return f"Carrito del Usuario ID {self.user_id} ({self.status})"

class CartItem(models.Model):
    """
    Modelo que representa un ítem dentro del carrito de compras
    """
    cart = models.ForeignKey(
        ShoppingCart,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    price_at_addition = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del producto al momento de agregar al carrito",
        default=Decimal('0.00')
    )

    class Meta:
        unique_together = ('cart', 'product_id')

    def __str__(self):
        # Actualizamos también el string representation
        return f"CartItem - UserID: {self.cart.user_id} - ProductID: {self.product_id}"