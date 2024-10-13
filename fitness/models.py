from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Sum

class Activity(models.Model):
    """
    Model representing a fitness activity logged by a user.
    """
    ACTIVITY_CHOICES = [
        ('Running', 'Running'),
        ('Cycling', 'Cycling'),
        ('Weightlifting', 'Weightlifting'),
        ('Swimming', 'Swimming'),
        ('Walking', 'Walking'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    duration = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Duration in minutes")
    distance = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0)], 
        blank=True, 
        null=True, 
        help_text="Distance in kilometers (optional for non-distance activities)"
    )
    calories_burned = models.PositiveIntegerField(validators=[MinValueValidator(0)], help_text="Calories burned during the activity")
    date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.activity_type} - {self.user.username}"

class Leaderboard(models.Model):
    """
    Model representing a leaderboard entry for a user, summarizing their activities by month and year.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    month = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1), 
            MaxValueValidator(12)
        ],
        help_text="Month of the year (1-12)"
    )
    year = models.PositiveIntegerField(validators=[MinValueValidator(2000)], help_text="Year of the activity")
    total_activities = models.PositiveIntegerField(default=0)
    total_distance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_calories_burned = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['user', 'month', 'year']
        ordering = ['-year', '-month', '-total_activities']

    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year} Leaderboard"

    @classmethod
    def update_leaderboard(cls, user, month, year):
        """
        Update the leaderboard entry for a user based on their activities for a specific month and year.
        Aggregates total activities, distance, and calories burned.
        """
        # Aggregate activities for the user by month and year
        activities = Activity.objects.filter(user=user, date__month=month, date__year=year)
        
        total_activities = activities.count()
        total_distance = activities.aggregate(Sum('distance'))['distance__sum'] or 0
        total_calories_burned = activities.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0

        # Create or update the leaderboard entry for the user
        leaderboard_entry, created = cls.objects.update_or_create(
            user=user, month=month, year=year,
            defaults={
                'total_activities': total_activities,
                'total_distance': total_distance,
                'total_calories_burned': total_calories_burned
            }
        )
        return leaderboard_entry
