from rest_framework import serializers
from .models import User, Category, News, Comment, Reaction, SubComment, CommentBase

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    news_count = serializers.IntegerField(source='news_set.count', read_only=True)
    class Meta:
        model = Category
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    reaction_count = serializers.IntegerField(source='reaction_set.count', read_only=True)
    author_name = serializers.CharField(source="author_id.name", read_only=True)
    author_avatar = serializers.CharField(source="author_id.avatar", read_only=True)
    class Meta:
        model = News
        fields = '__all__'

class SubCommentSerializer(serializers.ModelSerializer):
    sub_comment_count = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="user.name", read_only=True)
    author_avatar = serializers.CharField(source="user.avatar", read_only=True)

    class Meta:
        model = SubComment
        fields = '__all__'
    def get_sub_comment_count(self, obj):
        return obj.count_all_sub_comments()

class CommentSerializer(serializers.ModelSerializer):
    sub_comment_count = serializers.SerializerMethodField()
    author_name = serializers.CharField(source="user.name", read_only=True)
    author_avatar = serializers.CharField(source="user.avatar", read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

    def get_sub_comment_count(self, obj):
        return obj.count_all_sub_comments()

class CommentBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentBase
        fields = '__all__'

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = '__all__'
