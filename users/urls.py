from django.urls import path
from .views import LoginView, SignupView, UserInfoView, MoneyChargeView

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path('me/', UserInfoView.as_view()),
    path('charge-money/', MoneyChargeView.as_view())
]