# 学习资料接口：用户上传/共享/下载，以及管理端资料管理。
import os

from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LearningMaterial
from .serializers import (
    LearningMaterialSerializer,
    LearningMaterialCreateSerializer,
    LearningMaterialUpdateSerializer,
)


class LearningMaterialListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self, request):
        scope = (request.query_params.get('scope') or 'mine').strip().lower()
        keyword = (request.query_params.get('q') or '').strip()

        qs = LearningMaterial.objects.select_related('user__profile')

        if scope == 'shared':
            qs = qs.filter(is_shared=True)
        elif scope == 'all' and (request.user.is_staff or request.user.is_superuser):
            qs = qs.all()
        else:
            qs = qs.filter(user=request.user)

        if keyword:
            qs = qs.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(user__username__icontains=keyword)
                | Q(user__profile__nickname__icontains=keyword)
            )

        return qs.order_by('-created_at')

    def get(self, request):
        qs = self.get_queryset(request)
        data = LearningMaterialSerializer(qs, many=True, context={'request': request}).data
        return Response(data)

    def post(self, request):
        serializer = LearningMaterialCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        material = serializer.save()
        return Response(
            {
                'detail': '学习资料上传成功',
                'material': LearningMaterialSerializer(material, context={'request': request}).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LearningMaterialDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        material = get_object_or_404(LearningMaterial.objects.select_related('user__profile'), pk=pk)
        can_download = (
            material.is_shared
            or material.user_id == request.user.id
            or request.user.is_staff
            or request.user.is_superuser
        )
        if not can_download:
            return Response({'detail': '无权限下载该资料'}, status=status.HTTP_403_FORBIDDEN)
        if not material.file:
            return Response({'detail': '资料文件不存在'}, status=status.HTTP_404_NOT_FOUND)

        filename = os.path.basename(material.file.name)
        response = FileResponse(material.file.open('rb'), as_attachment=True, filename=filename)
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class LearningMaterialDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        material = get_object_or_404(LearningMaterial.objects.select_related('user__profile'), pk=pk)
        if material.user_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
            return None
        return material

    def patch(self, request, pk):
        material = self.get_object(request, pk)
        if not material:
            return Response({'detail': '无权限修改该资料'}, status=status.HTTP_403_FORBIDDEN)
        serializer = LearningMaterialUpdateSerializer(material, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'detail': '学习资料已更新',
            'material': LearningMaterialSerializer(material, context={'request': request}).data,
        })

    def delete(self, request, pk):
        material = self.get_object(request, pk)
        if not material:
            return Response({'detail': '无权限删除该资料'}, status=status.HTTP_403_FORBIDDEN)
        material.delete()
        return Response({'detail': '学习资料已删除'})
