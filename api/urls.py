from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (UserViewSet, CategoryViewSet,
                    NewsViewSet, CommentViewSet,
                    ReactionViewSet, SubCommentViewSet,
                    CommentBaseViewSet, CountRecordsView, NewsCountByMonthView, CountUserRecordsView)

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
    path('count/admin-dashboard', CountRecordsView.as_view(), name='count_records'),
    path('count/users-dashboard', CountUserRecordsView.as_view(), name='count_records_users'),
    path('count/news-by-month', NewsCountByMonthView.as_view(), name='count_news')
]