from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CategoryViewSet, NewsViewSet, CommentViewSet, ReactionViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'news', NewsViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'reactions', ReactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]