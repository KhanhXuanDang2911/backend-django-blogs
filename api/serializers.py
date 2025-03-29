from rest_framework import serializers
from .models import User, Category, News, Comment, Reaction, SubComment, CommentBase

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = '__all__'

    # Xóa validate_password để tránh mã hóa mật khẩu ở đây

    def create(self, validated_data):
        # Chắc chắn có password khi tạo mới
        if 'password' not in validated_data:
            raise serializers.ValidationError({"password": "Mật khẩu là bắt buộc"})

        # Không mã hóa ở đây nữa, để cho model tự xử lý
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Không mã hóa ở đây nữa, để cho model tự xử lý
        return super().update(instance, validated_data)

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
