import os

from rest_framework import serializers

from .models import LearningMaterial


class LearningMaterialSerializer(serializers.ModelSerializer):
    owner_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size_label = serializers.SerializerMethodField()
    visibility_label = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = LearningMaterial
        fields = (
            'id', 'title', 'description', 'owner_name', 'file_name', 'file_url', 'download_url',
            'file_size', 'file_size_label', 'is_shared', 'visibility_label',
            'can_edit', 'can_delete', 'created_at', 'updated_at',
        )

    def get_owner_name(self, obj):
        profile = getattr(obj.user, 'profile', None)
        nickname = getattr(profile, 'nickname', '') if profile else ''
        return nickname or obj.user.username

    def get_file_url(self, obj):
        if not obj.file:
            return ''
        request = self.context.get('request')
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_download_url(self, obj):
        request = self.context.get('request')
        url = f'/api/materials/{obj.pk}/download/'
        return request.build_absolute_uri(url) if request else url

    def get_file_name(self, obj):
        return os.path.basename(obj.file.name) if obj.file else ''

    def get_file_size_label(self, obj):
        size = int(obj.file_size or 0)
        if size < 1024:
            return f'{size} B'
        if size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        return f'{size / (1024 * 1024):.1f} MB'

    def get_visibility_label(self, obj):
        return '共享资料' if obj.is_shared else '私人资料'

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.is_superuser or obj.user_id == request.user.id

    def get_can_delete(self, obj):
        return self.get_can_edit(obj)


class LearningMaterialCreateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, max_length=120)
    description = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField()
    is_shared = serializers.BooleanField(required=False, default=False)

    def validate_file(self, value):
        max_size = 25 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('文件大小不能超过 25MB')
        return value

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        file_obj = validated_data['file']
        title = (validated_data.get('title') or '').strip()
        if not title:
            title = os.path.splitext(os.path.basename(file_obj.name))[0]
        material = LearningMaterial.objects.create(
            user=user,
            title=title,
            description=validated_data.get('description', '').strip(),
            file=file_obj,
            file_size=file_obj.size,
            is_shared=bool(validated_data.get('is_shared', False)),
        )
        return material


class LearningMaterialUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningMaterial
        fields = ('title', 'description', 'is_shared')

    def validate_title(self, value):
        return value.strip()
