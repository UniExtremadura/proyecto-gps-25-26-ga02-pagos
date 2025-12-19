from django.urls import path
from .views import OrderListCreateAPIView, OrderRetrieveAPIView, MyOrdersListAPIView

app_name = "orders"

urlpatterns = [
    path(
        "orders/",
        OrderListCreateAPIView.as_view(),
        name="order-list-create",
    ),
    path(
            'me/',
            MyOrdersListAPIView.as_view(),
            name='my-orders'
    ),

    path(
        "orders/<uuid:order_id>/",
        OrderRetrieveAPIView.as_view(),
        name="order-retrieve",
    ),

]
