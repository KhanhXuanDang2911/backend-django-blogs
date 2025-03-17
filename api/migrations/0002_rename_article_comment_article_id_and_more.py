# Generated by Django 5.1.7 on 2025-03-17 15:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='article',
            new_name='article_id',
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='user',
            new_name='user_id',
        ),
        migrations.RenameField(
            model_name='news',
            old_name='author',
            new_name='author_id',
        ),
        migrations.RenameField(
            model_name='reaction',
            old_name='news',
            new_name='news_id',
        ),
        migrations.RenameField(
            model_name='reaction',
            old_name='user',
            new_name='user_id',
        ),
    ]
