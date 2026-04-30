import bcrypt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import User

@api_view(['GET'])
def health(request):
    return Response({"status": "healthy", "framework": "Django 🚀"})

@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if User.objects.filter(username=username).exists():
        return Response({"message": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({"message": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Use pure bcrypt - NO Django wrapper
    salt = bcrypt.gensalt(rounds=12)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    user = User.objects.create(
        username=username,
        email=email,
        password_hash=hashed_password
    )
    
    return Response({"message": "User created successfully", "username": username})

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Pure bcrypt check
    stored_hash = user.password_hash.encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return Response({"message": "Login successful", "username": user.username})
    
    return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
