from django.http import Http404
from rest_framework import viewsets, status, filters
from rest_framework.exceptions import ValidationError
from .models import User, Category, News, Comment, Reaction, SubComment, CommentBase
from .serializers import UserSerializer, CategorySerializer, NewsSerializer, CommentSerializer, ReactionSerializer, SubCommentSerializer, CommentBaseSerializer
from .utils import custom_response, error_response
from django.db.models import Count

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

