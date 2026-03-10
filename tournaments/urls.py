from django.urls import path
from .views import TournamentListView, TournamentDetailView, TournamentCreateView, TournamentEditView

urlpatterns = [
    path("", TournamentListView.as_view(), name="tournament-list"),
    path("<int:id>/", TournamentDetailView.as_view(), name="tournament-detail"),
    path("create/", TournamentCreateView.as_view(), name="tournament-create"),
    path("<int:pk>/edit/",TournamentEditView.as_view(),name="tournament-edit"),
]