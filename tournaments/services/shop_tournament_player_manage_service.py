from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from rest_framework.exceptions import ValidationError

from tournaments.models import (
    Tournament,
    PokerTournament,
    TournamentEntry,
    BuyInEvent,
)

User = get_user_model()

class TournamentPlayerManageService:

    @staticmethod
    @transaction.atomic
    def approve_entry(
        owner,
        entry_id,
        table_number=None,
        seat_number=None
    ):

        entry = (
            TournamentEntry.objects
            .select_for_update()
            .get(id=entry_id)
        )

        tournament = (
            Tournament.objects
            .select_for_update()
            .get(id=entry.tournament_id)
        )

        if tournament.shop.owner != owner:
            raise ValidationError(
                "Not your tournament."
            )

        if entry.approval_status != "PENDING":
            raise ValidationError(
                "Entry already processed."
            )

        table_number = table_number or 0
        seat_number = seat_number or 0

        if tournament.game_type == (
            Tournament.GameTypeChoices.POKER
        ):

            poker_tournament = (
                PokerTournament.objects
                .select_for_update()
                .get(tournament=tournament)
            )

            latest_buyin = (
                BuyInEvent.objects
                .filter(entry=entry)
                .order_by("-created_at")
                .first()
            )

            if latest_buyin is None:
                raise ValidationError(
                    "Buy-in event not found."
                )

            if latest_buyin.type == (
                BuyInEvent.TypeChoices.ENTRY
            ):

                if (
                    poker_tournament.total_entries_cache
                    >= poker_tournament.max_entries
                ):
                    raise ValidationError(
                        "Tournament full."
                    )

                poker_tournament.total_entries_cache += 1

                poker_tournament.save(
                    update_fields=[
                        "total_entries_cache"
                    ]
                )

            elif latest_buyin.type == (
                BuyInEvent.TypeChoices.REENTRY
            ):

                poker_tournament.total_reentries_cache += 1

                poker_tournament.save(
                    update_fields=[
                        "total_reentries_cache"
                    ]
                )

            elif latest_buyin.type == (
                BuyInEvent.TypeChoices.ADDON
            ):

                poker_tournament.total_addons_cache += 1

                poker_tournament.save(
                    update_fields=[
                        "total_addons_cache"
                    ]
                )

            if latest_buyin.type != (
                BuyInEvent.TypeChoices.ADDON
            ):

                tournament.live_players_cache += 1

                tournament.save(
                    update_fields=[
                        "live_players_cache"
                    ]
                )

        else:

            if (
                tournament.live_players_cache
                >= tournament.max_participants
            ):
                raise ValidationError(
                    "Tournament full."
                )

            tournament.live_players_cache += 1

            tournament.save(
                update_fields=[
                    "live_players_cache"
                ]
            )

        entry.approval_status = "APPROVED"

        entry.approved_at = timezone.now()

        entry.approved_by = owner

        entry.table_number = table_number

        entry.seat_number = seat_number

        entry.save(
            update_fields=[
                "approval_status",
                "approved_at",
                "approved_by",
                "table_number",
                "seat_number",
            ]
        )

        return entry

    @staticmethod
    @transaction.atomic
    def reject_entry(owner, entry_id):

        entry = (
            TournamentEntry.objects
            .select_for_update()
            .get(id=entry_id)
        )

        tournament = (
            Tournament.objects
            .select_for_update()
            .get(id=entry.tournament_id)
        )

        if tournament.shop.owner != owner:

            raise ValidationError(
                "Not your tournament."
            )

        if entry.approval_status != "PENDING":

            raise ValidationError(
                "Entry already processed."
            )

        latest_buyin = (
            BuyInEvent.objects
            .filter(entry=entry)
            .order_by("-created_at")
            .first()
        )

        if latest_buyin is None:

            raise ValidationError(
                "Buy-in event not found."
            )

        player = (
            User.objects
            .select_for_update()
            .get(id=entry.player_id)
        )

        player.money += latest_buyin.amount

        player.save(
            update_fields=[
                "money"
            ]
        )

        if latest_buyin.type == (
            BuyInEvent.TypeChoices.ENTRY
        ):

            if entry.total_entries_cache > 0:

                entry.total_entries_cache -= 1

            entry.status = (
                TournamentEntry.StatusChoices.CANCELED
            )

        elif latest_buyin.type == (
            BuyInEvent.TypeChoices.REENTRY
        ):

            if entry.total_reentries_cache > 0:

                entry.total_reentries_cache -= 1

            entry.status = (
                TournamentEntry.StatusChoices.BUSTED
            )

        elif latest_buyin.type == (
            BuyInEvent.TypeChoices.ADDON
        ):

            if entry.total_addons_cache > 0:

                entry.total_addons_cache -= 1

        entry.approval_status = "REJECTED"

        entry.save(
            update_fields=[
                "status",
                "approval_status",
                "total_entries_cache",
                "total_reentries_cache",
                "total_addons_cache",
            ]
        )

        return entry

    @staticmethod
    @transaction.atomic
    def bust_player(owner, entry_id):

        entry = (
            TournamentEntry.objects
            .select_for_update()
            .get(id=entry_id)
        )

        tournament = (
            Tournament.objects
            .select_for_update()
            .get(id=entry.tournament_id)
        )

        if tournament.shop.owner != owner:

            raise ValidationError(
                "Not your tournament."
            )

        if entry.status != (
            TournamentEntry.StatusChoices.REGISTERED
        ):

            raise ValidationError(
                "Player not active."
            )

        entry.status = (
            TournamentEntry.StatusChoices.BUSTED
        )

        entry.busted_at = timezone.now()

        entry.save(
            update_fields=[
                "status",
                "busted_at"
            ]
        )

        if tournament.live_players_cache > 0:

            tournament.live_players_cache -= 1

            tournament.save(
                update_fields=[
                    "live_players_cache"
                ]
            )

        return entry