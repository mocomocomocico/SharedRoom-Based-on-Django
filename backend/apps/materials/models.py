# 学习资料模型：保存上传用户、文件、共享状态、大小和时间。
from pathlib import Path

from django.conf import settings
from django.db import models


class LearningMaterial(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_materials')
    title = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='learning_materials/%Y/%m/')
    file_size = models.PositiveBigIntegerField(default=0)
    is_shared = models.BooleanField(default=False, verbose_name='是否共享')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = '学习资料'
        verbose_name_plural = '学习资料'

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = getattr(self.file, 'size', 0) or 0
        if not self.title and self.file:
            self.title = Path(self.file.name).stem
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or self.file.name
