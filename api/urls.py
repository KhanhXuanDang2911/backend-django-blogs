from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CategoryViewSet, NewsViewSet, CommentViewSet, ReactionViewSet, SubCommentViewSet, \
    CommentBaseViewSet, RegisterView
from .views import LoginView, LogoutView, RefreshTokenView
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
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/refresh-token/", RefreshTokenView.as_view(), name="refresh-token"),
    path("auth/register/", RegisterView.as_view(), name="register"),

]