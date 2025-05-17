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

from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import timedelta
from collections import OrderedDict
from rest_framework.pagination import LimitOffsetPagination
from django.db import transaction

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

class NewsFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category__id")

    class Meta:
        model = News
        fields = ["category"]

class NewsPagination(LimitOffsetPagination):
    default_limit = None
    max_limit = 50
class NewsFilter(django_filters.FilterSet):
    author_id = django_filters.NumberFilter(field_name="author_id", lookup_expr="exact")  # 👈 Thêm filter author_id
    category = django_filters.NumberFilter(field_name="category", lookup_expr="exact")  # 👈 Thêm lọc category

    class Meta:
        model = News
        fields = ['author_id', 'category']
# class NewsViewSet(BaseViewSet):
#     queryset = News.objects.annotate(
#         reaction_count=Count('reaction')
#     ).select_related('category', 'author_id')
#     queryset = queryset.order_by('-created_at')
#     serializer_class = NewsSerializer
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter]
#     filterset_class = NewsFilter
#     search_fields = ['title']
#
#     pagination_class = NewsPagination
class NewsViewSet(BaseViewSet):
    queryset = News.objects.annotate(
        reaction_count=Count('reaction')
    ).select_related('category', 'author_id')
    queryset = queryset.order_by('-created_at')
    serializer_class = NewsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = NewsFilter
    search_fields = ['title']

    pagination_class = NewsPagination  # 👈 Vẫn giữ phân trang

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

class ReactionFilter(django_filters.FilterSet):
    news_id = django_filters.CharFilter(field_name="news_id__id")
    user_id = django_filters.CharFilter(field_name="user_id__id")

    class Meta:
        model = Reaction
        fields = ["news_id", "user_id"]

class ReactionViewSet(BaseViewSet):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ReactionFilter

class CountRecordsView(APIView):
    @staticmethod
    def get(request):
        data = {
            "user_count": User.objects.count(),
            "category_count": Category.objects.count(),
            "news_count": News.objects.count(),
            "reaction_count": Reaction.objects.count(),
            "comment_count": CommentBase.objects.count(),
        }
        return Response(data)

class CountUserRecordsView(APIView):
    @staticmethod
    def get(request):
        user_id = request.query_params.get('user_id')
        user = User.objects.filter(id=user_id).first()
        data = {
                "news_count": News.objects.filter(author_id=user).count(),
                "reaction_count": Reaction.objects.filter(user_id=user).count(),
                "comment_count": CommentBase.objects.filter(user=user).count(),
        }
        return Response(data)

class NewsCountByMonthView(APIView):
    @staticmethod
    def get(request):
        today = now().date()
        first_day_of_current_month = today.replace(day=1)
        start_date = (first_day_of_current_month - timedelta(days=365)).replace(day=1)

        news_count = (
            News.objects.filter(created_at__gte=start_date)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        data = OrderedDict()
        for i in range(12):
            month = (first_day_of_current_month - timedelta(days=i * 30)).replace(day=1)
            data[month.strftime('%Y-%m')] = 0

        for entry in news_count:
            key = entry["month"].strftime("%Y-%m")
            if key in data:
                data[key] = entry["count"]

        return Response(dict(data))


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
                "Tên đăng nhập hoặc mật khẩu không đúng",
                request.path
            )

        # Kiểm tra mật khẩu
        if not check_password(password, user.password):
            return error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Tên đăng nhập hoặc mật khẩu không đúng",
                request.path
            )

        if not user.is_active:
            return error_response(
                status.HTTP_403_FORBIDDEN,
                "Forbidden",
                "Tài khoản này đã bị vô hiệu hóa",
                request.path
            )

        # Tạo JWT token
        try:
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)

            # Thêm thông tin user vào response
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "avatar": str(user.avatar) if user.avatar else None,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser
            }

            return custom_response(
                status.HTTP_200_OK,
                "Đăng nhập thành công",
                {
                    "token": token,
                    "user": user_data
                }
            )
        except Exception as e:
            print(f"Lỗi tạo token: {str(e)}")
            return error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Internal Server Error",
                "Không thể tạo token",
                request.path
            )


class LogoutView(APIView):
    permission_classes = [AllowAny]  # Không cần xác thực vì không cần blacklist token

    def post(self, request):
        # Không cần xử lý gì với token vì phía client sẽ xóa token
        return custom_response(status.HTTP_200_OK, "Đăng xuất thành công")



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


class NewsImportView(APIView):
    """
    API endpoint that allows importing multiple news articles at once.
    """
    permission_classes = [AllowAny]  # No authentication required

    @transaction.atomic
    def post(self, request):
        """
        Import multiple news articles from a JSON array.
        Each news item should follow the structure of the News model.
        """
        news_data = request.data
        
        if not isinstance(news_data, list):
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                "Bad Request",
                "Request data must be a JSON array of news articles",
                request.path
            )
            
        if not news_data:
            return error_response(
                status.HTTP_400_BAD_REQUEST,
                "Bad Request",
                "Empty news data provided",
                request.path
            )
        
        results = []
        errors = []
        
        for index, item in enumerate(news_data):
            serializer = NewsSerializer(data=item)
            
            if serializer.is_valid():
                try:
                    news = serializer.save()
                    results.append({
                        "id": news.id,
                        "title": news.title,
                        "status": "success"
                    })
                except Exception as e:
                    errors.append({
                        "index": index,
                        "title": item.get("title", "Unknown title"),
                        "error": str(e)
                    })
            else:
                errors.append({
                    "index": index,
                    "title": item.get("title", "Unknown title"),
                    "error": serializer.errors
                })
        
        if errors:
            # If there are errors, return them along with successful imports
            return custom_response(
                status.HTTP_207_MULTI_STATUS,
                f"Imported {len(results)} out of {len(news_data)} articles with {len(errors)} errors",
                {
                    "imported": results,
                    "errors": errors,
                    "total_success": len(results),
                    "total_failure": len(errors),
                    "total_submitted": len(news_data)
                }
            )
        else:
            # All imports were successful
            return custom_response(
                status.HTTP_201_CREATED,
                f"Successfully imported {len(results)} articles",
                {
                    "imported": results,
                    "total_imported": len(results)
                }
            )

