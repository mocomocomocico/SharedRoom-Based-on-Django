# 共享自习室管理系统

这是一个前后端分离的共享自习室系统，包含用户端和管理端。

## 功能模块

### 用户端

- 账号注册、登录、个人资料维护。
- 查看座位并预约自由时间段。
- 查看预约历史、取消未开始预约。
- 每日学习打卡。
- 上传、共享、下载学习资料。

### 管理端

- 管理首页：查看座位、预约、用户、资料等运营统计。
- 座位管理：维护座位状态、区域、楼层和容量。
- 预约管理：按日期、状态、用户筛选预约记录，支持分页和取消预约。
- 用户管理：查询用户，编辑用户资料/角色/状态，登记违规并扣信用分。
- 资料管理：查看和处理用户上传的学习资料。

## 目录说明

详细代码结构请看 [`CODE_STRUCTURE.md`](./CODE_STRUCTURE.md)。

## 默认账号

运行后端默认数据命令后可使用。默认数据已扩展为 48 个座位，并给 `student1` 预置了更丰富的历史预约、取消记录和未来预约，方便直接查看首页、历史页和预约页效果：

- 管理员：`admin / admin123`
- 学生：`student1 / 12345678`
- 学生：`student2 / 12345678`
- 学生：`student3 / 12345678`
- 学生：`student4 / 12345678`
- 学生：`student5 / 12345678`

## 启动后端

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py reset_demo_data
python manage.py runserver
```

默认后端地址：`http://127.0.0.1:8000/`

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：`http://127.0.0.1:5173/`

## 重新生成前端生产文件

源码包不包含 `frontend/dist/`。需要部署时执行：

```bash
cd frontend
npm run build
```
