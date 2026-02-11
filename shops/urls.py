from django.urls import path
from .views import ShopCreateView

urlpatterns = [
    path('', ShopCreateView.as_view()),
]