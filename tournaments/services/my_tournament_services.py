from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentImage,
    TournamentEntry,
    BuyInEvent,
)


User = get_user_model()

class TournamentPlayerManageService:

    @staticmethod
    def get_my_tournaments(user):

        return (
            Tournament.objects
            .filter(
                entries__player=user
            )
            .select_related("shop")
            .order_by("-start_time")
            .distinct()
        )
    
    @staticmethod
    def get_my_tournament_detail(
        user,
        tournament_id
    ):

        entry = (
            TournamentEntry.objects
            .select_related(
                "tournament",
                "tournament__shop",
                "tournament__poker_tournament",
            )
            .prefetch_related(
                "buyin_events"
            )
            .filter(
                player=user,
                tournament_id=tournament_id
            )
            .first()
        )

        if not entry:

            raise ValidationError(
                "You are not registered for this tournament."
            )

        return entry