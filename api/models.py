from django.db import models

class User(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=255, default="Unknown")
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')])
    is_active = models.BooleanField(default=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(max_length=11, null=True)
    avatar = models.CharField(max_length=1000, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bio = models.TextField(null=True)

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(default = "No description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class News(models.Model):
    title = models.TextField()
    content = models.TextField()
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    status = models.CharField(max_length=20, choices=[('draft', 'Draft'), ('published', 'Published')])
    image = models.CharField(max_length=1000, null=True)
    published_at = models.DateTimeField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=[('approved', 'Approved'), ('spam', 'Spam')], default=('Approved', 'Approved'))


class Reaction(models.Model):
    type = models.CharField(max_length=20, choices=[('like', 'Like'), ('love', 'Love'), ('wow', 'Wow'), ('happy', 'Happy'), ('sad', 'Sad')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    news_id = models.ForeignKey(News, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
