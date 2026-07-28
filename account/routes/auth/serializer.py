from rest_framework import serializers
from account.models import User


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "avatar_url", "role", "xp_total"]
        read_only_fields = fields


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()