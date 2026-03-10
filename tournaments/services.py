from django.db import transaction
from .models import Tournament, TournamentImage

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