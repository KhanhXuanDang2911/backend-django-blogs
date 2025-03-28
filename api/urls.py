from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CategoryViewSet, NewsViewSet, CommentViewSet, ReactionViewSet, SubCommentViewSet, CommentBaseViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'news', NewsViewSet)
router.register(r'reactions', ReactionViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'sub-comments', SubCommentViewSet)
router.register(r'base-comments', CommentBaseViewSet, basename='base-comment')

urlpatterns = [
    path('', include(router.urls)),
]