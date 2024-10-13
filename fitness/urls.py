from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ActivityViewSet, LeaderboardViewSet
from . import views

# Create a router and register the viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')

urlpatterns = [
    path('', include(router.urls)),  # Include the router URLs
]
