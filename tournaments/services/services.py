from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from tournaments.models import Tournament, TournamentImage, TournamentEntry, BuyInEvent    

def create_tournament(*, shop, validated_data, images):
    """
    - Tournament Creation
    - Mutliple Images
    - Transcations
    """

    with transaction.atomic():
        tournament = Tournament.objects.create(
            shop=shop,
            **validated_data
        )

        for image in images:
            TournamentImage.objects.create(
                tournament=tournament,
                image=image
            )

    return tournament

def update_tournament(tournament, validated_data):
    for attr, value in validated_data.items():
        setattr(tournament, attr, value)

    tournament.save()

    return tournament

User = get_user_model()
class TournamentBuyInService:

    @staticmethod
    @transaction.atomic
    def execute(user, tournament, buyin_type):

        user = User.objects.select_for_update().get(id=user.id)
        tournament = Tournament.objects.select_for_update().get(id=tournament.id)

        if tournament.status not in ["WAITING", "RUNNING"]:
            raise ValidationError("Buy-in is not allowed for this tournament.")

        if buyin_type == BuyInEvent.TypeChoices.ENTRY:
            return TournamentBuyInService._handle_entry(user, tournament)

        elif buyin_type == BuyInEvent.TypeChoices.REENTRY:
            return TournamentBuyInService._handle_reentry(user, tournament)

        elif buyin_type == BuyInEvent.TypeChoices.ADDON:
            return TournamentBuyInService._handle_addon(user, tournament)

        raise ValidationError("Invalid buy-in type.")

    @staticmethod
    def _handle_entry(user, tournament):

        if TournamentEntry.objects.filter(
            player=user,
            tournament=tournament
        ).exists():
            raise ValidationError("Player already entered this tournament.")

        if tournament.total_entries_cache >= tournament.max_entries:
            raise ValidationError("Tournament entry limit reached.")

        if user.money < tournament.buy_in_amount:
            raise ValidationError("Not enough balance.")

        entry = TournamentEntry.objects.create(
            player=user,
            tournament=tournament,
            approval_status="PENDING"
        )

        BuyInEvent.objects.create(
            entry=entry,
            type=BuyInEvent.TypeChoices.ENTRY,
            amount=tournament.buy_in_amount
        )

        user.money -= tournament.buy_in_amount
        user.save(update_fields=["money"])

        return entry

    @staticmethod
    def _handle_reentry(user, tournament):

        if tournament.status != "RUNNING":
            raise ValidationError("Reentry allowed only during running tournament.")

        try:
            entry = TournamentEntry.objects.select_for_update().get(
                player=user,
                tournament=tournament
            )
        except TournamentEntry.DoesNotExist:
            raise ValidationError("Player has not entered this tournament.")

        if entry.status != TournamentEntry.StatusChoices.BUSTED:
            raise ValidationError("Reentry allowed only after bust.")

        if entry.total_reentries_cache >= tournament.max_reentries:
            raise ValidationError("Reentry limit reached.")

        if user.money < tournament.buy_in_amount:
            raise ValidationError("Not enough balance.")

        user.money -= tournament.buy_in_amount
        user.save(update_fields=["money"])

        entry.status = TournamentEntry.StatusChoices.REGISTERED
        entry.total_reentries_cache += 1
        entry.approval_status = "PENDING"
        entry.busted_at = None

        entry.save(update_fields=[
            "status",
            "total_reentries_cache",
            "approval_status",
            "busted_at"
        ])

        BuyInEvent.objects.create(
            entry=entry,
            type=BuyInEvent.TypeChoices.REENTRY,
            amount=tournament.buy_in_amount
        )

        return entry

    @staticmethod
    def _handle_addon(user, tournament):

        try:
            entry = TournamentEntry.objects.select_for_update().get(
                player=user,
                tournament=tournament
            )
        except TournamentEntry.DoesNotExist:
            raise ValidationError("Player has not entered this tournament.")

        if entry.status != TournamentEntry.StatusChoices.REGISTERED:
            raise ValidationError("Addon allowed only for active players.")

        if entry.total_addons_cache >= tournament.max_addons:
            raise ValidationError("Addon limit reached.")

        if user.money < tournament.addon_amount:
            raise ValidationError("Not enough balance.")

        user.money -= tournament.addon_amount
        user.save(update_fields=["money"])

        entry.total_addons_cache += 1
        entry.approval_status = "PENDING"

        entry.save(update_fields=[
            "total_addons_cache",
            "approval_status"
        ])

        BuyInEvent.objects.create(
            entry=entry,
            type=BuyInEvent.TypeChoices.ADDON,
            amount=tournament.addon_amount
        )

        return entry