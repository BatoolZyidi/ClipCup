"""
Clip Cup Authentication Views.
Provides register, login (JWT), refresh, and me endpoints.
Uses Django's built-in User model + djangorestframework-simplejwt.
"""

import logging
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger("clipcup.auth")


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "date_joined": user.date_joined.isoformat(),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_register(request):
    """
    POST /api/auth/register
    Body: { username, email, password, first_name?, last_name? }
    Returns: { user, access, refresh }
    """
    data = request.data
    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip()
    password = str(data.get("password", ""))
    first_name = str(data.get("first_name", "")).strip()
    last_name = str(data.get("last_name", "")).strip()

    if not username or not email or not password:
        return Response(
            {"error": "username, email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(password)
    except ValidationError as e:
        return Response({"error": " ".join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )

    refresh = RefreshToken.for_user(user)
    logger.info(f"New user registered: {username} ({email})")

    return Response(
        {
            "user": _user_payload(user),
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    """
    POST /api/auth/login
    Body: { username_or_email, password }
    Returns: { user, access, refresh }
    """
    data = request.data
    identifier = str(data.get("username_or_email", "")).strip()
    password = str(data.get("password", ""))

    if not identifier or not password:
        return Response(
            {"error": "username_or_email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Try username first, then email
    user = (
        User.objects.filter(username=identifier).first()
        or User.objects.filter(email=identifier).first()
    )

    if not user or not user.check_password(password):
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        return Response({"error": "Account is disabled."}, status=status.HTTP_403_FORBIDDEN)

    refresh = RefreshToken.for_user(user)
    logger.info(f"User logged in: {user.username}")

    return Response({
        "user": _user_payload(user),
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_refresh(request):
    """
    POST /api/auth/refresh
    Body: { refresh }
    Returns: { access }
    """
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh_token = str(request.data.get("refresh", ""))
    if not refresh_token:
        return Response({"error": "refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        return Response({"access": str(token.access_token)})
    except (TokenError, InvalidToken) as e:
        return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_me(request):
    """
    GET /api/auth/me
    Returns the currently authenticated user's profile.
    """
    return Response({"user": _user_payload(request.user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """
    POST /api/auth/logout
    Body: { refresh }
    Blacklists the refresh token (if blacklist app installed), otherwise just confirms.
    """
    try:
        refresh_token = str(request.data.get("refresh", ""))
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
    except Exception:
        pass  # Blacklist not enabled or token already expired — still return 200
    return Response({"detail": "Logged out successfully."})
