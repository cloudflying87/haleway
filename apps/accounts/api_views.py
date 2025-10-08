"""
API views for authentication.
"""
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model

from .serializers import UserSerializer, UserRegistrationSerializer

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    """API endpoint for user registration."""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer


class CurrentUserAPIView(generics.RetrieveAPIView):
    """API endpoint for current user info."""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
