from django.contrib import admin
from .models import Recipe, Comment

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'category', 'calorie_count', 'cooking_time', 'created_at')
    search_fields = ('title', 'created_by__username')
    list_filter = ('category', 'created_at', 'calorie_count')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'user', 'created_at')
    search_fields = ('recipe__title', 'user__username')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    