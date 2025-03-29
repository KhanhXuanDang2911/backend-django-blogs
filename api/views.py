from django.http import Http404
from rest_framework import viewsets, status, filters
from rest_framework.exceptions import ValidationError
from .models import User, Category, News, Comment, Reaction, SubComment, CommentBase
from .serializers import UserSerializer, CategorySerializer, NewsSerializer, CommentSerializer, ReactionSerializer, SubCommentSerializer, CommentBaseSerializer
from .utils import custom_response, error_response
from django.db.models import Count
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.utils.timezone import now
from .models import User
from .serializers import UserSerializer
from django.contrib.auth.hashers import check_password, make_password


class BaseViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
            return custom_response(status.HTTP_201_CREATED, "Add successful", response.data)
        except ValidationError as e:
            return error_response(status.HTTP_400_BAD_REQUEST, "Bad Request", str(e), request.path)

    def update(self, request, *args, **kwargs):
        try:
            response = super().update(request, *args, **kwargs)
            return custom_response(status.HTTP_202_ACCEPTED, "Update successful", response.data)
        except ValidationError as e:
            return error_response(status.HTTP_400_BAD_REQUEST, "Bad Request", str(e), request.path)

    def partial_update(self, request, *args, **kwargs):
        try:
            response = super().partial_update(request, *args, **kwargs)
            return custom_response(status.HTTP_204_NO_CONTENT, "Partial update successful")
        except ValidationError as e:
            return error_response(status.HTTP_400_BAD_REQUEST, "Bad Request", str(e), request.path)

    def destroy(self, request, *args, **kwargs):
        try:
            super().destroy(request, *args, **kwargs)
            return custom_response(status.HTTP_205_RESET_CONTENT, "Delete successful")
        except Http404:
            return error_response(status.HTTP_404_NOT_FOUND, "Not Found", "Object not found", request.path)

    def retrieve(self, request, *args, **kwargs):
        try:
            response = super().retrieve(request, *args, **kwargs)
            return custom_response(status.HTTP_200_OK, "Retrieve successful", response.data)
        except Http404:
            return error_response(status.HTTP_404_NOT_FOUND, "Not Found", "Object not found", request.path)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return custom_response(status.HTTP_200_OK, "List successful", response.data)

class UserViewSet(BaseViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class CategoryViewSet(BaseViewSet):
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        queryset = Category.objects.annotate(news_count=Count('news')).prefetch_related('news_set')

        limit = self.request.query_params.get('limit')
        order_by = self.request.query_params.get('order_by', '-id')

        allowed_fields = {'id', '-id', 'name', '-name', 'news_count', '-news_count', 'created_at', '-created_at'}
        if order_by not in allowed_fields:
            order_by = '-id'

        queryset = queryset.order_by(order_by)

        if limit is not None:
            return queryset[:int(limit)]
        return queryset

class NewsViewSet(BaseViewSet):
    queryset = News.objects.annotate(
        reaction_count=Count('reaction')
    ).select_related('category', 'author_id')
    serializer_class = NewsSerializer

    filter_backends = [filters.SearchFilter]
    search_fields = ['title']

class CommentBaseViewSet(BaseViewSet):
    queryset = CommentBase.objects.all()
    serializer_class = CommentBaseSerializer

class CommentViewSet(BaseViewSet):
    queryset = Comment.objects.select_related('user')
    queryset = queryset.order_by('-created_at')
    serializer_class = CommentSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['article__id']

class SubCommentViewSet(BaseViewSet):
    queryset = SubComment.objects.select_related('user')
    serializer_class = SubCommentSerializer
    queryset = queryset.order_by('-created_at')
    filter_backends = [filters.SearchFilter]
    search_fields = ['parent_comment__id']

class ReactionViewSet(BaseViewSet):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer



class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Invalid username or password",
                request.path
            )

        # Check encrypted password
        if not check_password(password, user.password):
            return error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Invalid username or password",
                request.path
            )

        if not user.is_active:
            return error_response(
                status.HTTP_403_FORBIDDEN,
                "Forbidden",
                "This account has been disabled",
                request.path
            )

        # Generate JWT token
        try:
            refresh = RefreshToken.for_user(user)
            return custom_response(
                status.HTTP_200_OK,
                "Login successful",
                {
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                }
            )
        except Exception as e:
            print(f"Token generation error: {str(e)}")
            return error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal Server Error",
                "Could not generate token",
                request.path
            )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            auth_header = request.headers.get('Authorization')
            print(auth_header)  # Debug: Check if "Bearer" exists
            token = RefreshToken(refresh_token)
            token.blacklist()  # Mark token as expired

            return custom_response(status.HTTP_200_OK, "Logout successful")
        except Exception:
            return error_response(status.HTTP_400_BAD_REQUEST, "Bad Request", "Invalid token", request.path)


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if not refresh_token:
                return error_response(status.HTTP_400_BAD_REQUEST, "Bad Request", "Refresh token is missing", request.path)

            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)

            return custom_response(
                status.HTTP_200_OK,
                "Token refreshed successfully",
                {"access_token": new_access_token}
            )
        except Exception:
            return error_response(status.HTTP_401_UNAUTHORIZED, "Unauthorized", "Invalid refresh token", request.path)



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        # Kiểm tra trùng username
        if User.objects.filter(username=username).exists():
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                "Username already exists",
                {"username": ["This username is already taken."]},
                request.path
            )

        # Kiểm tra trùng email
        if User.objects.filter(email=email).exists():
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                "Email already exists",
                {"email": ["This email is already registered."]},
                request.path
            )

        serializer = UserSerializer(data={
            "username": username,
            "name": request.data.get("name"),
            "email": email,
            "password": password,  # Password sẽ được mã hóa bởi model
            "role": "user",
            "is_active": True,
            "phone": request.data.get("phone", "")
        })

        if serializer.is_valid():
            user = serializer.save()
            return custom_response(
                status.HTTP_201_CREATED,
                "User registered successfully",
                {"id": user.id, "username": user.username, "email": user.email}
            )
        else:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                "Bad Request",
                serializer.errors,
                request.path
            )

