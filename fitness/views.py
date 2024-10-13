from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, filters
from .models import Activity, Leaderboard
from .serializers import UserSerializer, ActivitySerializer, LeaderboardSerializer
from datetime import timedelta
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework.decorators import action
# Custom permission class to restrict activity management to the owner


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners to edit or delete their own activities.
    """
    def has_object_permission(self, request, view, obj):
        # Read-only permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner of the activity
        return obj.user == request.user

class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard CRUD actions for users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optionally restricts the returned users to the currently authenticated user.
        Allows superusers to view all profiles.
        """
        if self.request.user.is_superuser:
            return User.objects.all()  # Allow superusers to view all profiles
        return User.objects.filter(id=self.request.user.id)

class ActivityViewSet(viewsets.ModelViewSet):
    """
    A viewset for CRUD operations on fitness activities.
    Users can only access and modify their own activities.
    """
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ['date', 'duration', 'calories_burned']
    ordering = ['-date']  # Default ordering by date (newest first)

    def get_queryset(self):
        """
        Only allow users to view their own activities with optional filters.
        """
        queryset = Activity.objects.filter(user=self.request.user)

        # Optional filtering by activity type
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)

        # Optional filtering by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(date__range=[start_date, end_date])

        return queryset

    def perform_create(self, serializer):
        """
        Set the logged-in user as the owner of the activity upon creation.
        """
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """
        Ensure the user can only update their own activity.
        """
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Ensure users can only delete their own activities.
        """
        if instance.user == self.request.user:
            instance.delete()

    @action(detail=False, methods=['get'], url_path='metrics')
    def activity_metrics(self, request):
        """
        Custom action to provide a summary of activity metrics:
        - Total duration
        - Total distance
        - Total calories burned
        - Weekly and monthly activity counts
        """
        user = request.user

        # Get the current date
        today = timezone.now().date()

        # Define the start of the week and month for metrics calculation
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Aggregate metrics for the user
        total_duration = Activity.objects.filter(user=user).aggregate(Sum('duration'))['duration__sum'] or 0
        total_distance = Activity.objects.filter(user=user).exclude(distance=None).aggregate(Sum('distance'))['distance__sum'] or 0
        total_calories_burned = Activity.objects.filter(user=user).aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
        
        # Weekly and monthly activity counts
        weekly_activities = Activity.objects.filter(user=user, date__gte=start_of_week).count()
        monthly_activities = Activity.objects.filter(user=user, date__gte=start_of_month).count()

        # Prepare the response data
        metrics = {
            'total_duration': total_duration,
            'total_distance': total_distance,
            'total_calories_burned': total_calories_burned,
            'weekly_activities': weekly_activities,
            'monthly_activities': monthly_activities,
        }

        return Response(metrics)

class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset to display the leaderboard, allowing users to see rankings.
    """
    queryset = Leaderboard.objects.all()
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination  # Add pagination

    def get_queryset(self):
        """
        Filter the leaderboard by month and year if provided in query.
        Default to current month and year.
        """
        month = self.request.query_params.get('month', timezone.now().month)
        year = self.request.query_params.get('year', timezone.now().year)
        return Leaderboard.objects.filter(month=month, year=year).order_by(
            '-total_activities', '-total_distance', '-total_calories_burned'
        )
