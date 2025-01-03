from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Post, Comment, Category


class PostAdmin(admin.ModelAdmin):
    list_display = ['date', 'name', 'title', 'created']
    search_fields = ['date', 'name']
    ordering = ['-created']


class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'created_at', 'modified_at']
    search_fields = ['author', 'created_at', 'modified_at']
    ordering = ['-created_at']


class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name', )}


class MyAdminSite(AdminSite):
    site_header = 'NewCovenant administration'


admin.site.register(Comment, CommentAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)