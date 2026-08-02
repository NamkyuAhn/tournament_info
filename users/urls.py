from django.urls import path
from .views import LoginView, SignupView, UserInfoView

urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path('me/', UserInfoView.as_view()),
]