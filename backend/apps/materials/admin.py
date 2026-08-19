from django.contrib import admin

from .models import LearningMaterial


@admin.register(LearningMaterial)
class LearningMaterialAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'is_shared', 'file_size', 'created_at')
    list_select_related = ('user',)
    search_fields = ('title', 'user__username', 'user__profile__nickname', 'description')
    list_filter = ('is_shared', 'created_at')
