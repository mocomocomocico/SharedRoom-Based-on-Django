"""一键重置演示数据。

运行方式：
    python manage.py reset_demo_data

该命令会清空现有演示数据，并重新生成：
- 1 个管理员账号 + 5 个学生账号；
- 72 个座位、5 个默认预约时段；
- 更丰富的 student1 默认预约历史、未来预约、取消记录；
- 其他学生的交叉预约、打卡、资料与违规示例。
"""
from datetime import datetime, timedelta, time
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import UserProfile, ViolationRecord
from apps.accounts.services import create_violation_record
from apps.checkins.models import DailyCheckIn
from apps.materials.models import LearningMaterial
from apps.reservations.models import Reservation
from apps.seats.models import Seat, TimeSlot


DEMO_PASSWORD = '12345678'

# 默认账号配置：信用分和违规次数由后续违规记录自动维护，避免手动字段不一致。
USER_SPECS = [
    dict(username='admin', password='admin123', email='admin@example.com', nickname='系统管理员', phone='13800000000', is_staff=True, is_superuser=True),
    dict(username='student1', password=DEMO_PASSWORD, email='student1@example.com', nickname='林书言', phone='13800000001', is_staff=False, is_superuser=False),
    dict(username='student2', password=DEMO_PASSWORD, email='student2@example.com', nickname='周亦晨', phone='13800000002', is_staff=False, is_superuser=False),
    dict(username='student3', password=DEMO_PASSWORD, email='student3@example.com', nickname='陈知夏', phone='13800000003', is_staff=False, is_superuser=False),
    dict(username='student4', password=DEMO_PASSWORD, email='student4@example.com', nickname='许安然', phone='13800000004', is_staff=False, is_superuser=False),
    dict(username='student5', password=DEMO_PASSWORD, email='student5@example.com', nickname='顾明远', phone='13800000005', is_staff=False, is_superuser=False),
]

TIME_SLOT_SPECS = [
    ('晨读时段', time(8, 0), time(10, 0), 1),
    ('上午时段', time(10, 0), time(12, 0), 2),
    ('下午时段', time(14, 0), time(17, 0), 3),
    ('晚间时段', time(18, 30), time(21, 30), 4),
    ('冲刺时段', time(21, 30), time(22, 30), 5),
]

# 座位平面图为 8 行 x 9 列，共 72 个座位。部分座位默认停用，用于演示不可预约状态。
# area_note 会展示在前端座位卡片中，便于一眼区分不同区域定位。
SEAT_ROWS = [
    ('A区', '靠窗自习区'),
    ('B区', '插座补能区'),
    ('C区', '安静专注区'),
    ('D区', '小组学习区'),
    ('E区', '开放阅读区'),
    ('F区', '考研冲刺区'),
    ('G区', '静音阅读区'),
    ('H区', '夜间学习区'),
]
SEAT_COL_COUNT = 9
INACTIVE_SEAT_CODES = {'S09', 'S20', 'S33', 'S45', 'S58', 'S67'}


class Command(BaseCommand):
    help = '重置系统为默认演示数据（用户、座位、预约、资料、违规与打卡记录）。'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('正在清理旧的演示数据...')
        self._clear_existing_data()
        self.stdout.write('正在创建默认账号...')
        users = self._create_users()
        self.stdout.write('正在创建默认时段与座位...')
        self._create_slots()
        seats = self._create_seats()
        self.stdout.write('正在创建预约、打卡与违规记录...')
        self._create_activity(users, seats)
        self.stdout.write('正在创建默认学习资料...')
        self._create_materials(users)
        self._print_success_summary()

    def _clear_existing_data(self):
        """删除所有演示数据和上传文件，确保每次重置后的状态完全一致。"""
        for material in LearningMaterial.objects.all():
            if material.file:
                material.file.delete(save=False)
        LearningMaterial.objects.all().delete()
        DailyCheckIn.objects.all().delete()
        ViolationRecord.objects.all().delete()
        Reservation.objects.all().delete()
        Seat.objects.all().delete()
        TimeSlot.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.exclude(username='').delete()

        media_root = Path(getattr(LearningMaterial._meta.get_field('file').storage, 'location', ''))
        if media_root.exists():
            materials_dir = media_root / 'learning_materials'
            if materials_dir.exists():
                for file_path in materials_dir.rglob('*'):
                    if file_path.is_file():
                        file_path.unlink()
                for dir_path in sorted([p for p in materials_dir.rglob('*') if p.is_dir()], reverse=True):
                    dir_path.rmdir()
                try:
                    materials_dir.rmdir()
                except OSError:
                    # 目录可能被系统文件占用，忽略即可，不影响数据库重置。
                    pass

    def _create_users(self):
        """创建默认登录账号；学生初始信用分均为 100，违规示例会自动扣分。"""
        users = {}
        for item in USER_SPECS:
            user = User.objects.create_user(
                username=item['username'],
                password=item['password'],
                email=item['email'],
                is_staff=item['is_staff'],
                is_superuser=item['is_superuser'],
                is_active=True,
            )
            UserProfile.objects.create(
                user=user,
                nickname=item['nickname'],
                phone=item['phone'],
                credit_score=100,
                violation_count=0,
            )
            users[item['username']] = user
        return users

    def _create_slots(self):
        """生成常用时段；保留自由预约能力，同时方便管理端查看时段配置。"""
        for name, start_time, end_time, sort_order in TIME_SLOT_SPECS:
            TimeSlot.objects.create(
                name=name,
                start_time=start_time,
                end_time=end_time,
                is_active=True,
                sort_order=sort_order,
            )

    def _seat_traits(self, row, col):
        """根据平面图坐标生成座位标签，减少手写座位配置的重复代码。"""
        # 两侧默认为靠窗位；偶数列提供插座，方便筛选演示。
        near_window = col in (1, SEAT_COL_COUNT)
        has_power = col in (2, 4, 6, 8)
        if near_window:
            seat_type = Seat.TYPE_WINDOW
        elif has_power:
            seat_type = Seat.TYPE_POWER
        elif row in (3, 6, 7):
            seat_type = Seat.TYPE_QUIET
        else:
            seat_type = Seat.TYPE_NORMAL
        return seat_type, has_power, near_window

    def _create_seats(self):
        """创建 72 个默认座位，覆盖靠窗、插座、安静区、夜间区、停用等多种演示状态。"""
        seats = []
        counter = 1
        for row_index, (area, area_note) in enumerate(SEAT_ROWS, start=1):
            for col in range(1, SEAT_COL_COUNT + 1):
                seat_code = f'S{counter:02d}'
                seat_type, has_power, near_window = self._seat_traits(row_index, col)
                seat = Seat.objects.create(
                    seat_code=seat_code,
                    area=area,
                    is_active=seat_code not in INACTIVE_SEAT_CODES,
                    note=area_note,
                    map_row=row_index,
                    map_col=col,
                    seat_type=seat_type,
                    has_power=has_power,
                    near_window=near_window,
                )
                seats.append(seat)
                counter += 1
        return seats

    def _aware_datetime(self, day, clock):
        return timezone.make_aware(datetime.combine(day, clock), timezone.get_current_timezone())

    def _create_reservation(self, *, user, seat, day, start, end, status, note='', cancelled_offset_minutes=20):
        """统一创建预约记录，并按状态自动补齐签到、签退或取消时间。"""
        start_dt = self._aware_datetime(day, start)
        end_dt = self._aware_datetime(day, end)
        reservation = Reservation.objects.create(
            user=user,
            seat=seat,
            reservation_date=day,
            start_time=start,
            end_time=end,
            status=status,
            note=note,
        )
        if status == Reservation.STATUS_COMPLETED:
            reservation.checkin_at = start_dt
            reservation.checkout_at = end_dt
        elif status == Reservation.STATUS_CHECKED_IN:
            reservation.checkin_at = start_dt
        elif status in (Reservation.STATUS_CANCELLED, Reservation.STATUS_EXPIRED):
            reservation.cancelled_at = start_dt + timedelta(minutes=cancelled_offset_minutes)
        reservation.save(update_fields=['checkin_at', 'checkout_at', 'cancelled_at', 'updated_at'])
        return reservation

    def _create_activity(self, users, seats):
        """生成预约、打卡和违规记录；student1 的默认数据会更加丰富。"""
        today = timezone.localdate()
        checked_days = {username: set() for username in users}

        def add_reservation(username, seat_index, day_offset, start, end, status, note=''):
            user = users[username]
            reservation = self._create_reservation(
                user=user,
                seat=seats[seat_index],
                day=today + timedelta(days=day_offset),
                start=start,
                end=end,
                status=status,
                note=note,
            )
            if status in (Reservation.STATUS_COMPLETED, Reservation.STATUS_CHECKED_IN):
                checked_days[username].add(reservation.reservation_date)
            return reservation

        # student1 是默认学生账号：提供更密集的历史趋势、状态分布和未来预约数据。
        student1_completed_plan = [
            (-13, 0, time(8, 30), time(10, 30), '晨读英语真题'),
            (-12, 1, time(14, 0), time(16, 30), '高数专题训练'),
            (-10, 2, time(18, 30), time(21, 0), '操作系统复盘'),
            (-9, 3, time(9, 0), time(11, 0), '概率论错题整理'),
            (-8, 4, time(15, 0), time(17, 30), '数据库实验报告'),
            (-6, 5, time(8, 0), time(10, 0), '晨间单词打卡'),
            (-5, 6, time(14, 0), time(17, 0), '数据结构刷题'),
            (-4, 7, time(19, 0), time(21, 30), '论文资料阅读'),
            (-3, 10, time(10, 0), time(12, 0), '线性代数复习'),
            (-2, 11, time(14, 30), time(17, 0), '计算机网络总结'),
            (-1, 12, time(18, 30), time(21, 0), '考前综合复盘'),
            (0, 13, time(8, 0), time(10, 0), '今日晨读完成记录'),
        ]
        for offset, seat_index, start, end, note in student1_completed_plan:
            add_reservation('student1', seat_index, offset, start, end, Reservation.STATUS_COMPLETED, note)

        # 额外补充一个月内的连续学习轨迹，让历史页趋势图、首页周/月报更有数据密度。
        # seat_index 使用取模轮换，既避免大量手写配置，也能让不同区域都有预约记录。
        student1_extra_topics = ['英语阅读精练', '高数真题计时', '专业课背诵', '错题本复盘', '论文检索', '算法刷题']
        for i, offset in enumerate(range(-30, -14)):
            start = time(8 + (i % 3) * 3, 0)
            end = time(10 + (i % 3) * 3, 0)
            topic = student1_extra_topics[i % len(student1_extra_topics)]
            add_reservation('student1', 22 + (i % 26), offset, start, end, Reservation.STATUS_COMPLETED, topic)

        student1_other_plan = [
            (-11, 14, time(18, 30), time(20, 30), Reservation.STATUS_CANCELLED, '临时课程冲突，主动取消'),
            (-7, 15, time(10, 0), time(12, 0), Reservation.STATUS_CANCELLED, '改为线上学习，主动取消'),
            (1, 16, time(19, 0), time(21, 0), Reservation.STATUS_BOOKED, '明晚复习高数'),
            (2, 17, time(14, 0), time(16, 30), Reservation.STATUS_BOOKED, '论文资料整理'),
            (4, 18, time(8, 0), time(10, 0), Reservation.STATUS_BOOKED, '周末晨读计划'),
            (6, 21, time(18, 30), time(21, 30), Reservation.STATUS_BOOKED, '考研英语长难句'),
            (8, 48, time(10, 0), time(12, 0), Reservation.STATUS_BOOKED, '周中专业课预习'),
            (10, 49, time(14, 0), time(17, 0), Reservation.STATUS_BOOKED, '实验报告完善'),
            (12, 50, time(18, 30), time(21, 30), Reservation.STATUS_BOOKED, '晚间冲刺复习'),
            (14, 51, time(8, 0), time(10, 0), Reservation.STATUS_BOOKED, '两周后晨读计划'),
            (-16, 52, time(14, 0), time(16, 0), Reservation.STATUS_CANCELLED, '临时更换学习地点'),
            (-18, 53, time(18, 30), time(20, 30), Reservation.STATUS_CANCELLED, '社团活动冲突'),
        ]
        for offset, seat_index, start, end, status_value, note in student1_other_plan:
            add_reservation('student1', seat_index, offset, start, end, status_value, note)

        # 其他学生数据用于丰富管理端列表、座位占用和状态分布。
        peer_plans = [
            ('student2', -12, 22, time(9, 0), time(11, 0), Reservation.STATUS_COMPLETED, '专业课预习'),
            ('student2', -8, 23, time(14, 0), time(16, 0), Reservation.STATUS_COMPLETED, '数据库练习'),
            ('student2', -5, 24, time(18, 30), time(20, 30), Reservation.STATUS_CANCELLED, '临时请假'),
            ('student2', -3, 25, time(15, 0), time(17, 0), Reservation.STATUS_COMPLETED, '英语阅读'),
            ('student2', 2, 26, time(8, 0), time(10, 0), Reservation.STATUS_BOOKED, '晨读计划'),
            ('student3', -11, 27, time(8, 30), time(10, 30), Reservation.STATUS_COMPLETED, '算法训练'),
            ('student3', -6, 28, time(14, 0), time(17, 0), Reservation.STATUS_COMPLETED, '线代专题'),
            ('student3', -1, 29, time(9, 30), time(11, 30), Reservation.STATUS_COMPLETED, '英语听力'),
            ('student3', 3, 30, time(14, 0), time(16, 0), Reservation.STATUS_BOOKED, '下午备考'),
            ('student4', -13, 31, time(10, 0), time(12, 0), Reservation.STATUS_COMPLETED, '实验报告整理'),
            ('student4', -7, 34, time(18, 30), time(21, 0), Reservation.STATUS_COMPLETED, '小组汇报准备'),
            ('student4', -2, 35, time(18, 30), time(20, 30), Reservation.STATUS_COMPLETED, '当前使用中示例前置记录'),
            ('student4', 0, 36, time(10, 0), time(12, 0), Reservation.STATUS_BOOKED, '临近期末复盘'),
            ('student5', -14, 37, time(10, 0), time(12, 0), Reservation.STATUS_COMPLETED, '计算机网络'),
            ('student5', -4, 38, time(14, 0), time(16, 0), Reservation.STATUS_COMPLETED, '数据库索引整理'),
            ('student5', 1, 39, time(8, 0), time(10, 0), Reservation.STATUS_BOOKED, '小组讨论前自习'),
        ]
        for username, offset, seat_index, start, end, status_value, note in peer_plans:
            add_reservation(username, seat_index, offset, start, end, status_value, note)

        # 管理端需要更丰富的列表和状态分布，因此为其他学生批量生成交叉预约。
        peer_names = ['student2', 'student3', 'student4', 'student5']
        peer_notes = ['期末复习', '实验预习', '英语听力', '小组讨论', '专业课整理']
        peer_status_cycle = [Reservation.STATUS_COMPLETED, Reservation.STATUS_COMPLETED, Reservation.STATUS_BOOKED, Reservation.STATUS_CANCELLED]
        for i, offset in enumerate(range(-28, 8)):
            username = peer_names[i % len(peer_names)]
            status_value = peer_status_cycle[i % len(peer_status_cycle)]
            seat_index = 12 + (i * 3 % 56)
            start = [time(8, 0), time(10, 0), time(14, 0), time(18, 30)][i % 4]
            end = [time(10, 0), time(12, 0), time(16, 0), time(21, 0)][i % 4]
            note = f"{peer_notes[i % len(peer_notes)]}批量演示记录"
            add_reservation(username, seat_index, offset, start, end, status_value, note)

        # 违规示例：通过服务函数创建，自动扣减信用分并累加违规次数。
        expired_student2 = add_reservation('student2', 40, -7, time(14, 0), time(16, 0), Reservation.STATUS_EXPIRED, '未签到示例')
        expired_student5_a = add_reservation('student5', 41, -10, time(8, 0), time(10, 0), Reservation.STATUS_EXPIRED, '晨读爽约示例')
        expired_student5_b = add_reservation('student5', 42, -2, time(18, 30), time(20, 30), Reservation.STATUS_EXPIRED, '晚间爽约示例')
        self._create_violation(users['student2'], users['admin'], expired_student2, today - timedelta(days=7), -15, '预约座位后未在 15 分钟内签到，系统记为爽约示例')
        self._create_violation(users['student5'], users['admin'], expired_student5_a, today - timedelta(days=10), -12, '晨读预约未签到，系统记为爽约示例')
        self._create_violation(users['student5'], users['admin'], expired_student5_b, today - timedelta(days=2), -10, '晚间预约未签到，系统记为爽约示例')

        for username, days in checked_days.items():
            for day in sorted(days):
                DailyCheckIn.objects.get_or_create(user=users[username], checkin_date=day)

    def _create_violation(self, user, admin, reservation, day, score_delta, reason):
        """创建违规记录后回写创建时间，让演示数据的时间线更真实。"""
        record, _ = create_violation_record(
            user=user,
            reservation=reservation,
            created_by=admin,
            violation_type=ViolationRecord.TYPE_NO_SHOW,
            reason=reason,
            score_delta=score_delta,
        )
        ViolationRecord.objects.filter(pk=record.pk).update(created_at=self._aware_datetime(day, time(9, 0)))

    def _create_materials(self, users):
        """创建少量文本资料文件，用于资料上传、共享和个人资料页展示。"""
        materials = [
            (users['student1'], '高数期中复习提纲', '按题型整理的高数重点与易错点。', 'math_review_outline.md', True, '# 高数复习\n\n1. 极限\n2. 导数\n3. 积分\n'),
            (users['student1'], '英语阅读笔记', '阅读理解高频词汇与句型整理。', 'english_reading_notes.txt', False, '英语阅读：长难句拆分、同义替换、段落主旨。\n'),
            (users['student1'], '考研周计划', 'student1 默认账号的周学习规划。', 'student1_weekly_plan.md', True, '# 本周计划\n\n- 高数真题 3 套\n- 英语阅读 8 篇\n- 专业课错题复盘\n'),
            (users['student2'], '操作系统实验总结', '实验环境、常见报错与处理办法。', 'os_lab_summary.txt', True, '操作系统实验：进程调度、内存管理、死锁分析。\n'),
            (users['student3'], '数据结构冲刺清单', '考前一周冲刺版知识清单。', 'data_structure_checklist.txt', True, '链表、栈队列、树、图、排序、查找。\n'),
            (users['student3'], '自习计划表', '个人自习计划安排。', 'study_plan.txt', False, '周一到周五晚间学习计划安排。\n'),
            (users['student4'], '线性代数错题集', '矩阵、行列式与特征值相关错题整理。', 'linear_algebra_mistakes.txt', True, '线代错题：矩阵初等变换、秩、特征值与二次型。\n'),
            (users['student4'], '概率论公式速查', '常用分布、期望方差与假设检验速查。', 'probability_formula_sheet.md', True, '# 概率论公式速查\n\n- 二项分布\n- 正态分布\n- 中心极限定理\n'),
            (users['student5'], '计算机网络复习卡片', '分层模型、TCP/IP、HTTP 与常见问答。', 'network_review_cards.txt', True, 'OSI 七层模型、三次握手、拥塞控制、HTTP 缓存。\n'),
            (users['student5'], '个人阅读清单', '私人可见的专业课阅读计划。', 'reading_list_private.txt', False, '本周阅读：数据库索引、事务隔离、查询优化。\n'),
            (users['student2'], '数据库实验备忘', 'SQL 查询、索引与事务实验注意事项。', 'database_lab_notes.txt', True, '数据库实验：DDL、DML、索引、事务 ACID。\n'),
            (users['student1'], '近一月复习复盘', '配合默认预约记录展示学习轨迹。', 'student1_month_review.md', True, '# 近一月复盘\n\n- 保持连续学习节奏\n- 每周整理错题\n- 周末做阶段测试\n'),
            (users['student1'], '座位偏好记录', '记录常用区域和偏好座位类型。', 'seat_preference_notes.txt', False, '优先选择靠窗位、插座位；晚间偏好 H 区。\n'),
        ]
        for owner, title, description, filename, is_shared, content in materials:
            material = LearningMaterial.objects.create(
                user=owner,
                title=title,
                description=description,
                is_shared=is_shared,
            )
            material.file.save(filename, ContentFile(content.encode('utf-8')), save=False)
            material.file_size = material.file.size or len(content.encode('utf-8'))
            material.save()

    def _print_success_summary(self):
        """输出登录信息和默认数据规模，便于重置后立刻测试。"""
        self.stdout.write(self.style.SUCCESS('默认数据已重置完成。'))
        self.stdout.write('管理员账号：admin / admin123')
        self.stdout.write(f'学生账号：student1 / {DEMO_PASSWORD}（已内置更多历史和未来预约）')
        self.stdout.write(f'学生账号：student2 / {DEMO_PASSWORD}')
        self.stdout.write(f'学生账号：student3 / {DEMO_PASSWORD}')
        self.stdout.write(f'学生账号：student4 / {DEMO_PASSWORD}')
        self.stdout.write(f'学生账号：student5 / {DEMO_PASSWORD}')
        self.stdout.write(f'默认座位数量：{Seat.objects.count()} 个；默认预约记录：{Reservation.objects.count()} 条')
