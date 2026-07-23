from django.db import models
from django.conf import settings
from shops.models import Shop
from users.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q

class Tournament(models.Model):

    class StatusChoices(models.TextChoices):
        WAITING = "WAITING", "Waiting"               
        RUNNING = "RUNNING", "Running"               # Entry Available
        REGI_CLOSED = "REGI_CLOSED", "Regi Closed"   # Entry Not Available
        FINISHED = "FINISHED", "Finished"            
        CANCELED = "CANCELED", "Canceled"            

    class GameTypeChoices(models.TextChoices):
        POKER = "POKER", "Poker"
        CHESS = "CHESS", "Chess"
        POKEMON_TCG = "POKEMON_TCG", "Pokémon TCG"

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="tournaments"
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    game_type = models.CharField(
        max_length=30,
        choices=GameTypeChoices.choices,
        default=GameTypeChoices.POKER
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.WAITING
    )

    registration_deadline = models.DateTimeField()

    start_time = models.DateTimeField()

    prize_structure = models.JSONField()

    entry_fee = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    max_participants = models.PositiveIntegerField()

    live_players_cache = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.registration_deadline < self.start_time:
            raise ValidationError(
                "Registration deadline must be equal to or after start time."
            )
        
    def __str__(self):
        return f"{self.title} ({self.shop.name})"
    
    class Meta:
        db_table = 'tournaments'
      
class TournamentImage(models.Model):

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="tournaments/"
    )

    is_primary = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.image.name} - {self.tournament.title}"

    class Meta:
        db_table = "tournament_images"
        ordering = ["-uploaded_at"]

class PokerTournament(models.Model):

    tournament = models.OneToOneField(
        Tournament,
        on_delete=models.CASCADE,
        related_name="poker_tournament"
    )

    max_entries = models.PositiveIntegerField()

    max_reentries = models.PositiveIntegerField(default=0)

    max_addons = models.PositiveIntegerField(default=0)

    starting_chips = models.PositiveIntegerField()

    early_chips = models.PositiveIntegerField(default=0)

    reentry_chips = models.PositiveIntegerField()

    addon_chips = models.PositiveIntegerField()

    blind_structure = models.JSONField()

    reentry_fee = models.PositiveIntegerField(default=0)

    addon_fee = models.PositiveIntegerField(default=0)

    total_entries_cache = models.PositiveIntegerField(default=0)

    total_reentries_cache = models.PositiveIntegerField(default=0)

    total_addons_cache = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'poker_tournaments'

class TournamentEntry(models.Model):

    class StatusChoices(models.TextChoices):
        REGISTERED = "REGISTERED", "Registered"
        BUSTED = "BUSTED", "Busted"
        CANCELED = "CANCELED", "Canceled"

    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tournament_entries"
    )

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="entries"
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.REGISTERED
    )

    total_entries_cache = models.PositiveIntegerField(default=1) 

    total_reentries_cache = models.PositiveIntegerField(default=0) 

    total_addons_cache = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    busted_at = models.DateTimeField(null=True, blank=True)

    table_number = models.PositiveIntegerField(null=True, blank=True)

    seat_number = models.PositiveIntegerField(null=True, blank=True)

    approval_status = models.CharField(
        max_length=20,
        choices=[
            ("PENDING", "Pending"),
            ("APPROVED", "Approved"),
            ("REJECTED", "Rejected"),
        ],
        default="PENDING",
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_entries"
    )

    class Meta:
        unique_together = ("player", "tournament")
        indexes = [
            models.Index(fields=["tournament"]),
            models.Index(fields=["player"]),
        ]
        db_table = 'tournament_entries'

        constraints = [
            models.UniqueConstraint(
                fields=["tournament", "table_number", "seat_number"],
                condition=Q(
                    table_number__isnull=False,
                    seat_number__isnull=False
                ),
            name="unique_tournament_seat"
            )
        ]

    def __str__(self):
        return f"{self.player.email} - {self.tournament.title}"
       
class BuyInEvent(models.Model):

    class TypeChoices(models.TextChoices):
        ENTRY = "ENTRY", "Entry"
        REENTRY = "REENTRY", "Reentry"
        ADDON = "ADDON", "Addon"   

    entry = models.ForeignKey(
        TournamentEntry,
        on_delete=models.CASCADE,
        related_name="buyin_events"
    )

    type = models.CharField(
        max_length=10,
        choices=TypeChoices.choices
    )

    amount = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entry", "type"]),
        ]
        db_table = 'buy_in_events'