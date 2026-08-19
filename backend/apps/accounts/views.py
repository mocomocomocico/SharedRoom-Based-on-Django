# 用户模块接口：个人资料、管理员用户列表/编辑/删除、违规记录管理。
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, ViolationRecord
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
    AdminUserUpdateSerializer,
    ViolationRecordSerializer,
    ViolationCreateSerializer,
)
from .services import create_violation_record

DEFAULT_RESET_PASSWORD = '123456'


def ensure_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def build_token_response(user):
    ensure_profile(user)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    })


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return build_token_response(user)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        user = authenticate(username=username, password=password)
        if not user:
            return Response({'detail': '账号或密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        return build_token_response(user)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_profile(request.user)
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.update(request.user, serializer.validated_data)
        ensure_profile(user)
        return Response({'detail': '个人信息已更新', 'user': UserSerializer(user).data})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'detail': '旧密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'detail': '密码修改成功'})


class MyViolationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_profile(request.user)
        qs = ViolationRecord.objects.select_related('user__profile', 'created_by__profile', 'reservation__seat').filter(user=request.user)
        return Response({
            'credit_score': request.user.profile.credit_score,
            'violation_count': request.user.profile.violation_count,
            'records': ViolationRecordSerializer(qs, many=True).data,
        })


class AdminViolationListCreateView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = ViolationRecord.objects.select_related('user__profile', 'created_by__profile', 'reservation__seat').all()
        user_value = (request.query_params.get('user_id') or '').strip()
        if user_value.isdigit():
            qs = qs.filter(user_id=int(user_value))
        return Response(ViolationRecordSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ViolationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(id=serializer.validated_data['user_id']).first()
        record, created = create_violation_record(
            user=user,
            reason=serializer.validated_data['reason'],
            score_delta=serializer.validated_data.get('score_delta', -10),
            violation_type=serializer.validated_data.get('violation_type', ViolationRecord.TYPE_MANUAL),
            created_by=request.user,
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({
            'detail': '违规记录已添加' if created else '已存在相同违规记录',
            'record': ViolationRecordSerializer(record).data,
            'user': UserSerializer(user).data,
        }, status=status_code)


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = User.objects.select_related('profile').all().order_by('-date_joined')
        keyword = request.query_params.get('q', '').strip()
        if keyword:
            qs = qs.filter(
                Q(username__icontains=keyword) |
                Q(email__icontains=keyword) |
                Q(profile__nickname__icontains=keyword) |
                Q(profile__phone__icontains=keyword)
            )
        return Response(UserSerializer(qs, many=True).data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get_object(self, pk):
        return User.objects.select_related('profile').filter(pk=pk).first()

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

    def patch(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.update(user, serializer.validated_data)
        ensure_profile(user)
        return Response({'detail': '用户已更新', 'user': UserSerializer(user).data})

    def post(self, request, pk):
        action = request.data.get('action', '').strip()
        if action != 'reset_password':
            return Response({'detail': '不支持的操作'}, status=status.HTTP_400_BAD_REQUEST)
        user = self.get_object(pk)
        if not user:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        user.set_password(DEFAULT_RESET_PASSWORD)
        user.save(update_fields=['password'])
        return Response({'detail': f'密码已重置为 {DEFAULT_RESET_PASSWORD}'})

    def delete(self, request, pk):
        if request.user.pk == pk:
            return Response({'detail': '不能删除当前登录账号'}, status=status.HTTP_400_BAD_REQUEST)
        user = self.get_object(pk)
        if not user:
            return Response({'detail': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({'detail': '用户已删除'})
