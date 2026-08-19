# 用户模块序列化器：负责前后端字段转换、注册校验和管理端用户编辑校验。
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from .models import UserProfile, ViolationRecord


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


class UserSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    credit_score = serializers.SerializerMethodField()
    violation_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser',
            'nickname', 'phone', 'role', 'credit_score', 'violation_count', 'last_login', 'date_joined'
        )

    def get_nickname(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.nickname if profile else ''

    def get_phone(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.phone if profile else ''

    def get_role(self, obj):
        return 'admin' if obj.is_staff or obj.is_superuser else 'user'

    def get_credit_score(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.credit_score if profile else 100

    def get_violation_count(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.violation_count if profile else 0


class ViolationRecordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    violation_type_label = serializers.SerializerMethodField()
    seat_code = serializers.SerializerMethodField()
    reservation_date = serializers.SerializerMethodField()

    class Meta:
        model = ViolationRecord
        fields = (
            'id', 'username', 'user_display_name', 'violation_type', 'violation_type_label',
            'reason', 'score_delta', 'seat_code', 'reservation_date', 'created_by_name', 'created_at'
        )

    def get_user_display_name(self, obj):
        profile = getattr(obj.user, 'profile', None)
        return getattr(profile, 'nickname', '') or obj.user.username

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return '系统自动'
        profile = getattr(obj.created_by, 'profile', None)
        return getattr(profile, 'nickname', '') or obj.created_by.username

    def get_violation_type_label(self, obj):
        return dict(ViolationRecord.TYPE_CHOICES).get(obj.violation_type, obj.violation_type)

    def get_seat_code(self, obj):
        return getattr(getattr(obj, 'reservation', None), 'seat', None).seat_code if getattr(obj, 'reservation', None) else ''

    def get_reservation_date(self, obj):
        return obj.reservation.reservation_date.isoformat() if obj.reservation else ''


class ViolationCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    reason = serializers.CharField(max_length=255)
    score_delta = serializers.IntegerField(default=-10)
    violation_type = serializers.ChoiceField(choices=ViolationRecord.TYPE_CHOICES, default=ViolationRecord.TYPE_MANUAL)

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('用户不存在')
        return value


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('账号已存在')
        return value

    @transaction.atomic
    def create(self, validated_data):
        nickname = validated_data.pop('nickname', '')
        phone = validated_data.pop('phone', '')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        UserProfile.objects.create(user=user, nickname=nickname, phone=phone)
        return user


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def update(self, instance, validated_data):
        profile = get_or_create_profile(instance)
        if 'email' in validated_data:
            instance.email = validated_data['email']
        if 'nickname' in validated_data:
            profile.nickname = validated_data['nickname']
        if 'phone' in validated_data:
            profile.phone = validated_data['phone']
        instance.save(update_fields=['email'])
        profile.save(update_fields=['nickname', 'phone'])
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '两次输入的新密码不一致'})
        return attrs


class AdminUserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    nickname = serializers.CharField(max_length=50, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    role = serializers.ChoiceField(choices=[('user', '用户'), ('admin', '管理员')], required=False)
    credit_score = serializers.IntegerField(required=False, min_value=0, max_value=100)

    def update(self, instance, validated_data):
        profile = get_or_create_profile(instance)
        if 'email' in validated_data:
            instance.email = validated_data['email']
        if 'is_active' in validated_data:
            instance.is_active = validated_data['is_active']
        if 'role' in validated_data:
            role = validated_data['role']
            instance.is_staff = role == 'admin'
            if role != 'admin':
                instance.is_superuser = False
        if 'nickname' in validated_data:
            profile.nickname = validated_data['nickname']
        if 'phone' in validated_data:
            profile.phone = validated_data['phone']
        if 'credit_score' in validated_data:
            profile.credit_score = validated_data['credit_score']
        instance.save()
        profile.save()
        return instance
