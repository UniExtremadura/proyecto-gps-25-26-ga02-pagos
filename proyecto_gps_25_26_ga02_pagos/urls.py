
from itertools import product

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

API_PREFIX = 'api/v1/'

urlpatterns = [
    path('admin/', admin.site.urls),

    # Conecta todas las URL de la app 'cart' bajo el prefijo 'api/v1/cart/'
    path(API_PREFIX, include(('orders.urls', 'orders'), namespace='orders')),

    path(API_PREFIX, include('cart.urls')),

    path(API_PREFIX, include('payments.urls')),

    path(f'{API_PREFIX}invoices/', include('invoices.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)