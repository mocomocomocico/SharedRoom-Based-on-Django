from rest_framework import serializers

from .models import DailyCheckIn


class DailyCheckInSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyCheckIn
        fields = ('id', 'checkin_date', 'created_at')
