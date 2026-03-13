from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from tournaments.models import TournamentEntry, Tournament

class TournamentPlayerManageService:

    @staticmethod
    @transaction.atomic
    def approve_entry(owner, entry_id, table_number=None, seat_number=None):

        entry = TournamentEntry.objects.select_for_update().get(id=entry_id)
        tournament = Tournament.objects.select_for_update().get(id=entry.tournament_id)

        if tournament.shop.owner != owner:
            raise ValidationError("Not your tournament.")

        if entry.approval_status != "PENDING":
            raise ValidationError("Entry already processed.")

        if tournament.total_entries_cache >= tournament.max_entries:
            raise ValidationError("Tournament full.")

        table_number = table_number or 0
        seat_number = seat_number or 0

        entry.approval_status = "APPROVED"
        entry.approved_at = timezone.now()
        entry.approved_by = owner
        entry.table_number = table_number
        entry.seat_number = seat_number

        entry.save(update_fields=[
            "approval_status",
            "approved_at",
            "approved_by",
            "table_number",
            "seat_number"
        ])

        tournament.total_entries_cache += 1
        tournament.live_players_cache += 1
        tournament.save(update_fields=[
            "total_entries_cache",
            "live_players_cache"
        ])

        return entry

    @staticmethod
    @transaction.atomic
    def reject_entry(owner, entry_id):

        entry = TournamentEntry.objects.select_for_update().get(id=entry_id)
        tournament = entry.tournament

        if tournament.shop.owner != owner:
            raise ValidationError("Not your tournament.")

        if entry.approval_status != "PENDING":
            raise ValidationError("Entry already processed.")

        entry.approval_status = "REJECTED"
        entry.save(update_fields=["approval_status"])

        return entry

    @staticmethod
    @transaction.atomic
    def bust_player(owner, entry_id):

        entry = TournamentEntry.objects.select_for_update().get(id=entry_id)
        tournament = entry.tournament

        if tournament.shop.owner != owner:
            raise ValidationError("Not your tournament.")

        if entry.status != "REGISTERED":
            raise ValidationError("Player not active.")

        entry.status = "BUSTED"
        entry.busted_at = timezone.now()

        entry.save(update_fields=["status", "busted_at"])

        tournament.live_players_cache -= 1
        tournament.save(update_fields=["live_players_cache"])

        return entry