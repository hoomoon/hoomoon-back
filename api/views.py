from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Plan, Deposit
from .serializers import PlanSerializer, DepositSerializer

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset         = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

class DepositViewSet(viewsets.ModelViewSet):
    queryset         = Deposit.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
