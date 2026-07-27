from django.urls import path

from tournaments.views.views import (
    TournamentListView,
    TournamentDetailView,
    TournamentCreateView,
    TournamentEditView,
    TournamentBuyInView,
)

from tournaments.views.shop_tournament_views import (
    ShopTournamentListView,
    ShopTournamentDetailView,
    EntryApproveView,
    EntryRejectView,
    EntryBustView,
    TournamentCancelView,
)

from tournaments.views.my_tournament_views import (
    MyTournamentListView,
    MyTournamentDetailView,
)


urlpatterns = [
    path(
        "",
        TournamentListView.as_view(),
        name="tournament-list",
    ),

    path(
        "create/",
        TournamentCreateView.as_view(),
        name="tournament-create",
    ),

    path(
        "my-shop-tournaments/",
        ShopTournamentListView.as_view(),
        name="shop-tournament-list",
    ),

    path(
        "my-shop-tournaments/<int:pk>/",
        ShopTournamentDetailView.as_view(),
        name="shop-tournament-detail",
    ),

    path(
        "<int:tournament_id>/buyin/",
        TournamentBuyInView.as_view(),
        name="tournament-buyin",
    ),

    path(
        "<int:pk>/edit/",
        TournamentEditView.as_view(),
        name="tournament-edit",
    ),

    path(
        "<int:id>/",
        TournamentDetailView.as_view(),
        name="tournament-detail",
    ),

    path(
        "entries/<int:entry_id>/approve/",
        EntryApproveView.as_view(),
        name="entry-approve",
    ),

    path(
        "entries/<int:entry_id>/reject/",
        EntryRejectView.as_view(),
        name="entry-reject",
    ),

    path(
        "entries/<int:entry_id>/bust/",
        EntryBustView.as_view(),
        name="entry-bust",
    ),

    path(
        "my-tournaments/",
        MyTournamentListView.as_view(),
        name="my-tournaments",
    ),

    path(
        "my-tournaments/<int:tournament_id>/",
        MyTournamentDetailView.as_view(),
        name="my-tournament-detail",
    ),

    path(
        "<int:tournament_id>/cancel/",
        TournamentCancelView.as_view(),
        name="tournament-cancel",
    ),
]