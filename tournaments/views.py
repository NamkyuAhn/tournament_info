from django.shortcuts import render
from rest_framework import generics
from .models import Tournament
from .serializers import TournamentListSerializer, TournamentDetailSerializer

class TournamentListView(generics.ListAPIView):
    serializer_class = TournamentListSerializer

    def get_queryset(self):
        queryset = Tournament.objects.select_related("shop")

        status = self.request.query_params.get("status")

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-start_time")

class TournamentDetailView(generics.RetrieveAPIView):
    serializer_class = TournamentDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Tournament.objects.select_related("shop")