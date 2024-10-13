from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Activity, Leaderboard

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        Create a new user with the validated data.
        """
        user = User.objects.create_user(**validated_data)
        return user


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'activity_type', 'duration', 'distance', 'calories_burned', 'date', 'user']
        read_only_fields = ['user']
        extra_kwargs = {
            'distance': {'required': False, 'allow_null': True}  # Allow null or no distance for non-distance activities
        }

    def validate(self, data):
        """
        Validate required fields for the Activity model.
        - Ensure duration, activity_type, and date are provided.
        - Handle optional distance for non-distance activities.
        """
        activity_type = data.get('activity_type')
        duration = data.get('duration')
        date = data.get('date')

        # Ensure required fields are provided
        if not activity_type:
            raise serializers.ValidationError({'activity_type': 'This field is required.'})
        if duration is None:
            raise serializers.ValidationError({'duration': 'This field is required.'})
        if not date:
            raise serializers.ValidationError({'date': 'This field is required.'})

        # If distance-based activity, ensure distance is provided
        if activity_type in ['Running', 'Cycling', 'Swimming', 'Walking']:
            if data.get('distance') is None:
                raise serializers.ValidationError({'distance': 'This field is required for distance-based activities.'})

        return data


class LeaderboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leaderboard
        fields = ['user', 'total_activities', 'total_distance', 'total_calories_burned', 'month', 'year']
