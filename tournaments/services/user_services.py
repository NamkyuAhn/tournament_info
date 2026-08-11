from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

from tournaments.models import (
    Tournament,
    TournamentEntry,
    PokerTournament,
    BuyInEvent
)

User = get_user_model()

class TournamentBuyInService:

    @staticmethod
    @transaction.atomic
    def execute(user, tournament, buyin_type):

        user = User.objects.select_for_update().get(
            id=user.id
        )

        tournament = Tournament.objects.select_for_update().get(
            id=tournament.id
        )

        if tournament.status not in [
            Tournament.StatusChoices.WAITING,
            Tournament.StatusChoices.RUNNING,
        ]:

            raise ValidationError(
                "Buy-in is not allowed for this tournament."
            )

        if buyin_type == BuyInEvent.TypeChoices.ENTRY:

            return TournamentBuyInService._handle_entry(
                user,
                tournament
            )

        if buyin_type == BuyInEvent.TypeChoices.REENTRY:

            return TournamentBuyInService._handle_reentry(
                user,
                tournament
            )

        if buyin_type == BuyInEvent.TypeChoices.ADDON:

            return TournamentBuyInService._handle_addon(
                user,
                tournament
            )

        raise ValidationError(
            "Invalid buy-in type."
        )

    @staticmethod
    def _handle_entry(user, tournament):

        entry = (
            TournamentEntry.objects
            .select_for_update()
            .filter(
                player=user,
                tournament=tournament
            )
            .first()
        )

        if entry:

            if (
                entry.status
                != TournamentEntry.StatusChoices.CANCELED
                or entry.approval_status != "REJECTED"
            ):

                raise ValidationError(
                    "Player already entered this tournament."
                )

        TournamentBuyInService._validate_entry_capacity(
            tournament
        )

        if user.money < tournament.entry_fee:

            raise ValidationError(
                "Not enough balance."
            )

        if entry:

            entry.status = (
                TournamentEntry.StatusChoices.REGISTERED
            )

            entry.approval_status = "PENDING"

            entry.total_entries_cache += 1

            entry.save(
                update_fields=[
                    "status",
                    "approval_status",
                    "total_entries_cache",
                ]
            )

        else:

            entry = TournamentEntry.objects.create(
                player=user,
                tournament=tournament,
                approval_status="PENDING",
                total_entries_cache=1,
            )

        BuyInEvent.objects.create(
            entry=entry,
            type=BuyInEvent.TypeChoices.ENTRY,
            amount=tournament.entry_fee
        )

        user.money -= tournament.entry_fee

        user.save(
            update_fields=[
                "money"
            ]
        )

        return entry

    @staticmethod
    def _handle_reentry(user, tournament):

        if tournament.game_type != (
            Tournament.GameTypeChoices.POKER
        ):

            raise ValidationError(
                "Reentry is only available for poker tournaments."
            )

        if tournament.status != (
            Tournament.StatusChoices.RUNNING
        ):

            raise ValidationError(
                "Reentry allowed only during running tournament."
            )

        poker_tournament = (
            PokerTournament.objects
            .select_for_update()
            .get(tournament=tournament)
        )

        entry = TournamentBuyInService._get_entry(
            user,
            tournament
        )

        if entry.status != (
            TournamentEntry.StatusChoices.BUSTED
        ):

            raise ValidationError(
                "Reentry allowed only after bust."
            )

        if (
            entry.total_reentries_cache
            >= poker_tournament.max_reentries
        ):

            raise ValidationError(
                "Reentry limit reached."
            )

        if user.money < poker_tournament.reentry_fee:

            raise ValidationError(
                "Not enough balance."
            )

        user.money -= poker_tournament.reentry_fee

        user.save(
            update_fields=["money"]
        )

        entry.status = (
            TournamentEntry.StatusChoices.REGISTERED
        )

        entry.total_reentries_cache += 1

        entry.approval_status = "PENDING"

        entry.busted_at = None

        entry.table_number = None

        entry.seat_number = None

        entry.save(
            update_fields=[
                "status",
                "total_reentries_cache",
                "approval_status",
                "busted_at",
                "table_number",
                "seat_number",
            ]
        )

        BuyInEvent.objects.create(
            entry=entry,
            type=BuyInEvent.TypeChoices.REENTRY,
            amount=poker_tournament.reentry_fee
        )

        return entry

    @staticmethod
    def _handle_addon(user, tournament):

        if tournament.game_type != (
            Tournament.GameTypeChoices.POKER
        ):

            raise ValidationError(
                "Addon is only available for poker tournaments."
            )

        if tournament.status != (
            Tournament.StatusChoices.RUNNING
        ):

            raise ValidationError(
                "Addon allowed only during running tournament."
            )

        poker_tournament = (
            PokerTournament.objects
            .select_for_update()
            .get(tournament=tournament)
        )

        entry = TournamentBuyInService._get_entry(
            user,
            tournament
        )

        if entry.status != (
            TournamentEntry.StatusChoices.REGISTERED
        ):

            raise ValidationError(
                "Addon allowed only for active players."
            )

        if (
            entry.total_addons_cache
            >= poker_tournament.max_addons
        ):

            raise ValidationError(
                "Addon limit reached."
            )

        if user.money < poker_tournament.addon_fee:

            raise ValidationError(
                "Not enough balance."
            )

        user.money -= poker_tournament.addon_fee

        user.save(
            update_fields=["money"]
        )

        entry.total_addons_cache += 1

        entry.approval_status = "PENDING"

        entry.save(
            update_fields=[
                "total_addons_cache",
                "approval_status",
            ]
        )

        BuyInEvent.objects.create(
            entry=entry,
            type=BuyInEvent.TypeChoices.ADDON,
            amount=poker_tournament.addon_fee
        )

        return entry

    @staticmethod
    def _validate_entry_capacity(tournament):

        if tournament.game_type == (
            Tournament.GameTypeChoices.POKER
        ):

            poker_tournament = (
                PokerTournament.objects
                .select_for_update()
                .get(tournament=tournament)
            )

            if (
                poker_tournament.total_entries_cache
                >= poker_tournament.max_entries
            ):

                raise ValidationError(
                    "Tournament entry limit reached."
                )

        else:

            if (
                tournament.live_players_cache
                >= tournament.max_participants
            ):

                raise ValidationError(
                    "Tournament participant limit reached."
                )

    @staticmethod
    def _get_entry(user, tournament):

        try:

            return (
                TournamentEntry.objects
                .select_for_update()
                .get(
                    player=user,
                    tournament=tournament
                )
            )

        except TournamentEntry.DoesNotExist:

            raise ValidationError(
                "Player has not entered this tournament."
            )


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