# FairCourt - 校园场地公平预约系统

## 项目简介

FairCourt是一个基于Flask的校园场地公平预约系统，旨在解决传统"抢订"模式的不公平问题。系统采用智能分配算法，结合信用评分机制，为学生提供公平、稳定的场地预约服务。

## 核心特性

### 🎯 公平分配机制
- **预约池模式**: 学生提交申请后，系统每日22:00统一分配
- **智能权重算法**: 根据历史成功率和信用分动态调整优先级
- **加权随机选择**: 避免完全按权重排序，增加公平性

### 📊 信用评分系统
- **初始信用分**: 新用户100分
- **动态调整**: 根据预约成功率和爽约情况调整
- **爽约惩罚**: 每次爽约扣10分，影响后续预约优先级

### 🔄 候补队列机制
- **自动候补**: 未分配成功的申请自动进入候补队列
- **实时递补**: 有人取消预约时，自动分配给候补队列中的下一位

### 📈 预约限制
- **周次数限制**: 每人每周最多预约3次
- **防止霸占**: 有效分散预约资源

## API接口文档

### 学生模块 (`/api/student`)

#### 1. 学生注册
```http
POST /api/student/register
Content-Type: application/json

{
    "student_id": "2021001",
    "name": "张三",
    "email": "zhangsan@example.com",
    "password": "password123",
    "phone": "13800138000"
}
```

#### 2. 学生登录
```http
POST /api/student/login
Content-Type: application/json

{
    "student_id": "2021001",
    "password": "password123"
}
```

#### 3. 提交预约申请
```http
POST /api/student/apply
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "time_slot_id": 1
}
```

#### 4. 取消预约申请
```http
POST /api/student/cancel
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "application_id": 1
}
```

#### 5. 直接预约未申请的场地
```http
POST /api/student/reserve_direct
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "time_slot_id": 1
}
```

#### 6. 获取申请状态
```http
GET /api/student/status
Authorization: Bearer <access_token>
```

#### 7. 查看历史预约与违约记录
```http
GET /api/student/records
Authorization: Bearer <access_token>
```

#### 8. 获取信用评分
```http
GET /api/student/credit
Authorization: Bearer <access_token>
```

### 场地与场次模块 (`/api`)

#### 1. 获取所有启用的场地信息
```http
GET /api/courts
```

#### 2. 查询可申请的场次
```http
GET /api/timeslots/available?date=2024-01-15&court_id=1
```

#### 3. 查询某天的预约状态
```http
GET /api/timeslots/reserve_status?date=2024-01-15
```

## 安装和运行

### 1. 环境要求
- Python 3.8+
- Flask 2.3+
- SQLite (默认) 或其他数据库

### 2. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 运行应用
```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

### 4. 初始化数据
首次运行时，系统会自动创建数据库表并初始化示例场地数据：
- 羽毛球场1号 (体育馆一层)
- 羽毛球场2号 (体育馆一层)
- 羽毛球场3号 (体育馆二层)
- 羽毛球场4号 (体育馆二层)

## 系统架构

### 数据模型
- **Student**: 学生信息和信用评分
- **Court**: 场地信息
- **TimeSlot**: 时间段
- **Application**: 预约申请
- **Reservation**: 预约记录
- **WeeklyStats**: 周统计数据

### 调度任务
- **22:00**: 执行公平分配算法
- **01:00**: 更新信用评分
- **02:00**: 清理过期数据
- **每10分钟**: 处理候补队列

### 公平分配算法
1. 收集所有待处理申请
2. 按时间段分组
3. 计算每个学生的优先级权重
4. 使用加权随机选择分配场地
5. 未分配的申请进入候补队列

### 优先级权重计算
```python
priority_weight = (1 - success_rate) * (credit_score / 100)
```
- `success_rate`: 历史预约成功率
- `credit_score`: 当前信用分

## 配置说明

### 环境变量
- `DATABASE_URL`: 数据库连接字符串
- `JWT_SECRET_KEY`: JWT密钥
- `SECRET_KEY`: Flask密钥

### 系统配置 (config.py)
- `MAX_WEEKLY_RESERVATIONS`: 每周最大预约次数 (默认3次)
- `ALLOCATION_TIME`: 每日分配时间 (默认22:00)
- `ADVANCE_DAYS`: 提前预约天数 (默认2天)

## 使用示例

### 学生使用流程
1. **注册账号**: 使用学号、姓名、邮箱注册
2. **登录系统**: 获取访问令牌
3. **查看可用场次**: 浏览可预约的时间段
4. **提交申请**: 选择心仪的时间段提交申请
5. **等待分配**: 系统在22:00自动分配
6. **查看结果**: 检查申请状态和预约记录

### 管理员功能
- 创建新的时间段
- 批量创建时间段
- 查看预约统计

## 技术特点

### 高可用性
- 后台调度任务自动处理分配
- 异常处理和日志记录
- 数据库事务保证一致性

### 扩展性
- 模块化设计
- RESTful API
- 支持多种数据库

### 安全性
- JWT身份验证
- 密码加密存储
- 输入验证和错误处理

## 开发计划

- [ ] 添加邮件通知功能
- [ ] 实现微信小程序接口
- [ ] 增加管理员后台界面
- [ ] 支持多种场地类型
- [ ] 添加预约评价系统

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

MIT License 