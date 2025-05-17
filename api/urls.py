from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, CategoryViewSet, NewsViewSet, CommentViewSet, ReactionViewSet, SubCommentViewSet, \
    CommentBaseViewSet, RegisterView
from .views import LoginView, LogoutView
from .views import (UserViewSet, CategoryViewSet,
                    NewsViewSet, CommentViewSet,
                    ReactionViewSet, SubCommentViewSet,
                    CommentBaseViewSet, CountRecordsView, NewsCountByMonthView, CountUserRecordsView, NewsImportView)
from django.urls import path, include

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'news', NewsViewSet)
router.register(r'reactions', ReactionViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'sub-comments', SubCommentViewSet)
router.register(r'base-comments', CommentBaseViewSet, basename='base-comment')

urlpatterns = [
    path("news/import/", NewsImportView.as_view(), name="news_import"),
    path('', include(router.urls)),
    path('count/admin-dashboard', CountRecordsView.as_view(), name='count_records'),
    path('count/users-dashboard', CountUserRecordsView.as_view(), name='count_records_users'),
    path('count/news-by-month', NewsCountByMonthView.as_view(), name='count_news'),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/register/", RegisterView.as_view(), name="register"),
]