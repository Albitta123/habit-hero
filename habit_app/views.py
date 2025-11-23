from rest_framework import viewsets, status
from rest_framework.permissions import (
    IsAuthenticated,
    IsAdminUser,
    AllowAny
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes
from .models import Category, Habit, HabitCheckin
from .serializers import CategorySerializer, HabitSerializer, HabitCheckinSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        # Allow read-only access to all; admin required for write operations
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminUser()]


class HabitViewSet(viewsets.ModelViewSet):
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]  # Require login for all actions

    def get_queryset(self):
        user = self.request.user
        # Admins see all habits, normal users see only their own
        if user.is_staff:
            return Habit.objects.all()
        return Habit.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        habit = self.get_object()
        user = self.request.user
        if habit.owner != user and not user.is_staff:
            raise PermissionDenied("You cannot update another user's habit.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.owner != user and not user.is_staff:
            raise PermissionDenied("You cannot delete another user's habit.")
        instance.delete()


class HabitCheckinViewSet(viewsets.ModelViewSet):
    serializer_class = HabitCheckinSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return HabitCheckin.objects.all()
        elif user.is_authenticated:
            return HabitCheckin.objects.filter(habit__owner=user)
        else:
            return HabitCheckin.objects.none()  # or all if you want anonymous to view all


    def perform_create(self, serializer):
        habit = serializer.validated_data.get("habit")
        user = self.request.user

        # If user is anonymous (not authenticated), allow post without ownership check
        if user.is_authenticated:
            # For authenticated users, only allow if admin or habit owner
            if not user.is_staff and habit.owner.id != user.id:
                raise PermissionDenied("Cannot check in to a habit you do not own.")

        # For anonymous users or passed checks, save the check-in
        serializer.save()




    def perform_update(self, serializer):
        habit = self.get_object()
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication required.")
        if habit.owner != user and not user.is_staff:
            raise PermissionDenied("You cannot update another user's habit.")
        serializer.save()



    def perform_destroy(self, instance):
        # Normal user cannot delete others' check-ins
        if not self.request.user.is_staff and instance.habit.owner != self.request.user:
            raise PermissionDenied("You cannot delete another user's check-in.")
        instance.delete()


@api_view(["GET"])
@permission_classes([AllowAny])
def debug_auth(request):
    return Response({
        "HTTP_AUTHORIZATION": request.META.get("HTTP_AUTHORIZATION"),
        "Authorization_header": request.headers.get("Authorization"),
    })
