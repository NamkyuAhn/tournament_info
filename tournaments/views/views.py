from rest_framework import generics


from tournaments.models import Tournament
from tournaments.pagination import TournamentPagination

from tournaments.serializers.serializers import (
    TournamentListSerializer,
    TournamentDetailSerializer,
)



class TournamentListView(generics.ListAPIView):

    serializer_class = TournamentListSerializer
    pagination_class = TournamentPagination
    
    def get_queryset(self):

        queryset = (
            Tournament.objects
            .select_related("shop")
            .prefetch_related("images")
        )

        tournament_status = (
            self.request.query_params.get("status")
        )

        game_type = (
            self.request.query_params.get("game_type")
        )

        if tournament_status:

            queryset = queryset.filter(
                status=tournament_status
            )

        if game_type:

            queryset = queryset.filter(
                game_type=game_type
            )

        return queryset.order_by(
            "start_time"
        )


class TournamentDetailView(generics.RetrieveAPIView):

    serializer_class = TournamentDetailSerializer

    lookup_field = "id"

    def get_queryset(self):

        return (
            Tournament.objects
            .select_related(
                "shop"
            )
            .prefetch_related(
                "images"
            )
        )

