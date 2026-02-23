from django.urls import path
from .views import TournamentListView, TournamentDetailView

urlpatterns = [
    path("", TournamentListView.as_view(), name="tournament-list"),
    path("<int:id>/", TournamentDetailView.as_view(), name="tournament-detail"),
]