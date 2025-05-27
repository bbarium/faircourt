# FairCourt 前端

FairCourt 校园场地公平预约系统的前端界面，采用现代化的响应式设计，提供直观易用的用户体验。

## 功能特性

### 🏠 首页
- 系统介绍和特色功能展示
- 快速导航到主要功能
- 响应式设计，适配各种设备

### 🏢 场地信息
- 查看所有可用场地
- 场地详细信息（位置、容量、类型等）
- 卡片式布局，信息清晰

### 📅 预约申请
- 日期选择（限制为明天到一周后）
- 场地筛选功能
- 时间段状态可视化
- 一键申请预约

### 📊 申请状态
- 我的申请列表
- 预约记录查看
- 实时状态更新
- 取消申请功能

### 👤 个人中心
- 基本信息展示
- 信用评分可视化
- 使用统计数据
- 个人预约历史

## 技术栈

- **HTML5**: 语义化标记
- **CSS3**: 现代化样式，CSS变量，Flexbox/Grid布局
- **JavaScript ES6+**: 模块化开发，异步处理
- **Font Awesome**: 图标库
- **Fetch API**: HTTP请求处理

## 项目结构

```
frontend/
├── index.html          # 主页面
├── css/
│   └── style.css      # 样式文件
├── js/
│   ├── api.js         # API接口管理
│   ├── auth.js        # 用户认证管理
│   └── main.js        # 主要功能逻辑
└── README.md          # 说明文档
```

## 快速开始

### 1. 启动后端服务

确保后端服务已经启动并运行在 `http://localhost:5000`

```bash
cd backend
python app.py
```

### 2. 启动前端服务

可以使用任何静态文件服务器，例如：

#### 使用Python内置服务器
```bash
cd frontend
python -m http.server 8080
```

#### 使用Node.js serve
```bash
cd frontend
npx serve -s . -l 8080
```

#### 使用Live Server (VS Code扩展)
在VS Code中安装Live Server扩展，右键点击`index.html`选择"Open with Live Server"

### 3. 访问应用

打开浏览器访问 `http://localhost:8080`

## 核心功能说明

### 用户认证
- 支持学生注册和登录
- JWT令牌认证
- 自动保持登录状态
- 安全退出登录

### 预约流程
1. 用户登录系统
2. 选择预约日期（明天到一周后）
3. 查看可用时间段
4. 提交预约申请
5. 等待系统分配（每日22:00）
6. 查看申请结果

### 状态管理
- 实时显示申请状态
- 支持取消待处理申请
- 查看历史预约记录
- 信用评分跟踪

### 响应式设计
- 移动端友好界面
- 自适应布局
- 触摸友好的交互
- 优化的加载性能

## API集成

前端通过RESTful API与后端通信：

### 学生接口
- `POST /api/student/register` - 学生注册
- `POST /api/student/login` - 学生登录
- `POST /api/student/apply` - 提交预约申请
- `POST /api/student/cancel` - 取消预约申请
- `GET /api/student/status` - 获取申请状态
- `GET /api/student/records` - 查看历史记录
- `GET /api/student/credit` - 获取信用评分

### 场地接口
- `GET /api/courts` - 获取场地信息
- `GET /api/timeslots/available` - 查询可用时间段
- `GET /api/timeslots/reserve_status` - 查询预约状态

## 用户界面特性

### 现代化设计
- 清新的配色方案
- 一致的视觉语言
- 直观的图标使用
- 流畅的动画效果

### 交互体验
- 即时反馈提示
- 加载状态指示
- 错误处理机制
- 确认对话框

### 可访问性
- 语义化HTML结构
- 键盘导航支持
- 屏幕阅读器友好
- 高对比度设计

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 开发说明

### 代码结构
- `api.js`: 封装所有API调用，统一错误处理
- `auth.js`: 用户认证逻辑，状态管理
- `main.js`: 页面逻辑，数据渲染，事件处理

### 样式组织
- CSS变量统一管理主题色彩
- 模块化样式，便于维护
- 响应式断点设计
- 动画和过渡效果

### 最佳实践
- 异步操作错误处理
- 用户输入验证
- 状态同步机制
- 性能优化考虑

## 故障排除

### 常见问题

1. **无法连接后端**
   - 检查后端服务是否启动
   - 确认API_BASE_URL配置正确
   - 检查网络连接

2. **登录失败**
   - 验证学号和密码格式
   - 检查后端数据库连接
   - 查看浏览器控制台错误

3. **页面显示异常**
   - 清除浏览器缓存
   - 检查JavaScript控制台错误
   - 确认所有资源文件加载正常

### 调试技巧
- 使用浏览器开发者工具
- 查看Network标签页的API请求
- 检查Console标签页的错误信息
- 使用Application标签页查看本地存储

## 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 完整的用户界面实现
- 所有核心功能支持
- 响应式设计完成

## 贡献指南

1. Fork项目仓库
2. 创建功能分支
3. 提交代码更改
4. 发起Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。 