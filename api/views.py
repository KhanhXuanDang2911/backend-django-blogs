from django.http import Http404
from rest_framework import viewsets, status, filters
from rest_framework.exceptions import ValidationError
from .models import User, Category, News, Comment, Reaction, SubComment, CommentBase
from .serializers import UserSerializer, CategorySerializer, NewsSerializer, CommentSerializer, ReactionSerializer, SubCommentSerializer, CommentBaseSerializer
from .utils import custom_response, error_response
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models.functions import TruncMonth
from django.utils.timezone import now
from datetime import timedelta
from collections import OrderedDict
from rest_framework.pagination import LimitOffsetPagination

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

class NewsViewSet(BaseViewSet):
    queryset = News.objects.annotate(
        reaction_count=Count('reaction')
    ).select_related('category', 'author_id')
    queryset = queryset.order_by('-created_at')
    serializer_class = NewsSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = NewsFilter
    search_fields = ['title']

    pagination_class = NewsPagination

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
        user_id = 8  # Hardcode user_id = 8
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