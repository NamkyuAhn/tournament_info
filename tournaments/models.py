from django.db import models
from django.conf import settings
from shops.models import Shop
from django.core.exceptions import ValidationError

class Tournament(models.Model):

    class StatusChoices(models.TextChoices):
        WAITING = "WAITING", "Waiting"               
        RUNNING = "RUNNING", "Running"               # Entry Available
        REGI_CLOSED = "REGI_CLOSED", "Regi Closed"   # Entry Not Available
        FINISHED = "FINISHED", "Finished"            
        CANCELED = "CANCELED", "Canceled"            

    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name="tournaments"
    )

    title = models.CharField(max_length=200)

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.WAITING
    )

    max_entries = models.PositiveIntegerField()

    max_reentries = models.PositiveIntegerField(default=0)

    registration_deadline = models.DateTimeField()

    start_time = models.DateTimeField()

    starting_chips = models.PositiveIntegerField()

    reentry_chips = models.PositiveIntegerField()

    addon_chips = models.PositiveIntegerField()

    max_addons = models.PositiveIntegerField(default=0)

    blind_structure = models.JSONField()

    prize_structure = models.JSONField()

    buy_in_amount = models.PositiveIntegerField()

    addon_amount = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    total_entries_cache = models.PositiveIntegerField(default=0)

    total_reentries_cache = models.PositiveIntegerField(default=0)

    total_addons_cache = models.PositiveIntegerField(default=0)

    live_players_cache = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.registration_deadline < self.start_time:
            raise ValidationError(
                "Registration deadline must be after start time."
            )
        
    def __str__(self):
        return f"{self.title} ({self.shop.name})"
      
class TournamentImage(models.Model):

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name="images"
    )

    file_url = models.URLField(max_length=500)

    file_name = models.CharField(max_length=255)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name} - {self.tournament.title}"

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

    class Meta:
        unique_together = ("player", "tournament")
        indexes = [
            models.Index(fields=["tournament"]),
            models.Index(fields=["player"]),
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