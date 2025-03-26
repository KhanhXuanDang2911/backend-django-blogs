from rest_framework import serializers
from .models import User, Category, News, Comment, Reaction

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
    comment_count = serializers.IntegerField(source='comment_set.count', read_only=True)
    reaction_count = serializers.IntegerField(source='reaction_set.count', read_only=True)
    author_name = serializers.CharField(source="author_id.name", read_only=True)
    author_avatar = serializers.CharField(source="author_id.avatar", read_only=True)
    class Meta:
        model = News
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = '__all__'
