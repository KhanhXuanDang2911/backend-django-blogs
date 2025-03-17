from django.contrib import admin
from .models import User, Category, News, Comment, Reaction

# Đăng ký các model vào trang admin
admin.site.register(User)
admin.site.register(Category)
admin.site.register(News)
admin.site.register(Comment)
admin.site.register(Reaction)
