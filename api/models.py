from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=128)
    name = models.CharField(max_length=45)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')])
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Cần thiết để đăng nhập admin
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=11)
    avatar = models.CharField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'  # Django dùng trường này để xác thực user
    REQUIRED_FIELDS = ['email', 'name']  # Các trường bắt buộc khi tạo superuser

    def save(self, *args, **kwargs):
        # Chỉ mã hóa nếu password không phải đã mã hóa
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=45, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class News(models.Model):
    title = models.TextField()
    content = models.TextField()
    excerpt = models.TextField(default=title)
    author_id = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('published', 'Published')])
    image = models.CharField(max_length=1000, blank=True, null=True)
    published_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CommentBase(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = False

    def count_all_sub_comments(self):
        if not hasattr(self, "pr"):
            return 0

        count = self.pr.count()
        for sub_comment in self.pr.all():
            count += sub_comment.count_all_sub_comments()
        return count


class Comment(CommentBase):
    commentbase_ptr = models.OneToOneField(CommentBase, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    article = models.ForeignKey(News, on_delete=models.CASCADE)

class SubComment(CommentBase):
    commentbase_ptr = models.OneToOneField(CommentBase, on_delete=models.CASCADE, parent_link=True, primary_key=True)
    parent_comment = models.ForeignKey(CommentBase, on_delete=models.CASCADE, related_name='pr')

class Reaction(models.Model):
    type = models.CharField(max_length=20, choices=[('love', 'Love'), ('like', 'Like'), ('dislike', 'Dislike'), ('wow', 'Wow'),
                                                    ('sad', 'Sad')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    news_id = models.ForeignKey(News, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

