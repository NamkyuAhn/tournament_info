from rest_framework import serializers
from .models import Tournament

class TournamentListSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = Tournament
        fields = [
            "id",
            "title",
            "shop_name",
            "status",
            "start_time",
            "registration_deadline",
            "buy_in_amount",
            "total_entries_cache",
            "live_players_cache",
        ]

class TournamentDetailSerializer(serializers.ModelSerializer):
    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = Tournament
        fields = "__all__"