from django.urls import path

from .views import (
    ShopCreateView,
    ShopUpdateView,
)


urlpatterns = [
    path(
        "",
        ShopCreateView.as_view(),
        name="shop-create",
    ),

    path(
        "me/",
        ShopUpdateView.as_view(),
        name="shop-update",
    ),
]