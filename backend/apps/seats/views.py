# 座位接口：提供座位查询、管理端新增/编辑/删除座位和时间段。
from datetime import date as date_cls

from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reservations.services import expire_overdue_reservations
from .models import Seat, TimeSlot
from .serializers import SeatSerializer, SeatCreateUpdateSerializer, TimeSlotSerializer


class TimeSlotListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        slots = TimeSlot.objects.all()
        return Response(TimeSlotSerializer(slots, many=True).data)

    def post(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        serializer = TimeSlotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slot = TimeSlot.objects.create(**serializer.validated_data)
        return Response(TimeSlotSerializer(slot).data, status=status.HTTP_201_CREATED)


class TimeSlotDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        serializer = TimeSlotSerializer(slot, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TimeSlotSerializer(slot).data)

    def delete(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        name = slot.name
        slot.delete()
        return Response({'detail': f'时段 {name} 已删除'})


class SeatListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expire_overdue_reservations()
        reservation_date = request.query_params.get('date')
        if reservation_date:
            try:
                parsed_date = date_cls.fromisoformat(reservation_date)
            except ValueError:
                return Response({'detail': '日期格式错误'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            parsed_date = date_cls.today()
        serializer = SeatSerializer(Seat.objects.all(), many=True, context={'reservation_date': parsed_date, 'request': request})
        return Response(serializer.data)

    def post(self, request):
        if not request.user.is_staff and not request.user.is_superuser:
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        payload = request.data.copy()
        max_row = Seat.objects.aggregate(value=Max('map_row')).get('value') or 1
        max_col = Seat.objects.filter(map_row=max_row).aggregate(value=Max('map_col')).get('value') or 0
        if not payload.get('map_row'):
            payload['map_row'] = max_row
        if not payload.get('map_col'):
            payload['map_col'] = max_col + 1
        serializer = SeatCreateUpdateSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        seat = serializer.save()
        return Response(SeatCreateUpdateSerializer(seat).data, status=status.HTTP_201_CREATED)


class SeatDetailView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        seat = get_object_or_404(Seat, pk=pk)
        serializer = SeatCreateUpdateSerializer(seat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SeatCreateUpdateSerializer(seat).data)

    def delete(self, request, pk):
        seat = get_object_or_404(Seat, pk=pk)
        seat_code = seat.seat_code
        seat.delete()
        return Response({'detail': f'座位 {seat_code} 已删除'})
