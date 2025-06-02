// API配置
const API_BASE_URL = 'http://localhost:5000';

// API接口类
class API {
    constructor() {
        this.baseURL = API_BASE_URL;
        this.token = localStorage.getItem('token');
    }

    // 设置认证令牌
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    }

    // 获取认证头
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    // 通用请求方法
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // GET请求
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    // POST请求
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT请求
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE请求
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // 学生相关API
    async registerStudent(studentData) {
        return this.post('/api/student/register', studentData);
    }

    async loginStudent(credentials) {
        const response = await this.post('/api/student/login', credentials);
        if (response.token) {
            this.setToken(response.token);
        }
        return response;
    }

    async getStudentStatus() {
        return this.get('/api/student/status');
    }

    async getStudentRecords() {
        return this.get('/api/student/records');
    }

    async getStudentCredit() {
        return this.get('/api/student/credit');
    }

    async submitApplication(applicationData) {
        return this.post('/api/student/apply', applicationData);
    }

    async cancelApplication(applicationData) {
        return this.post('/api/student/cancel', applicationData);
    }

    async reserveDirect(reservationData) {
        return this.post('/api/student/reserve_direct', reservationData);
    }

    // 场地相关API
    async getCourts() {
        return this.get('/api/courts');
    }

    async getCampusCourts(campusId) {
        return this.get(`/api/courts/${campusId}`);
    }

    async getAvailableTimeSlots(date, courtId = null) {
        let endpoint = `/api/timeslots/available?date=${date}`;
        if (courtId) {
            endpoint += `&court_id=${courtId}`;
        }
        return this.get(endpoint);
    }

    async getReserveStatus(date, courtId = null) {
        let endpoint = `/api/timeslots/reserve_status?date=${date}`;
        if (courtId) {
            endpoint += `&court_id=${courtId}`;
        }
        return this.get(endpoint);
    }

    // 退出登录
    logout() {
        this.setToken(null);
    }
}

// 创建全局API实例
const api = new API();

// 工具函数
const utils = {
    // 格式化日期
    formatDate(date) {
        if (typeof date === 'string') {
            date = new Date(date);
        }
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
    },

    // 格式化时间
    formatTime(time) {
        return time.substring(0, 5); // HH:MM
    },

    // 格式化日期时间
    formatDateTime(datetime) {
        const date = new Date(datetime);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 获取状态显示文本
    getStatusText(status) {
        const statusMap = {
            'pending': '待分配',
            'approved': '已通过',
            'rejected': '已拒绝',
            'cancelled': '已取消',
            'completed': '已完成',
            'no_show': '未到场'
        };
        return statusMap[status] || status;
    },

    // 获取状态CSS类
    getStatusClass(status) {
        const classMap = {
            'pending': 'status-pending',
            'approved': 'status-approved',
            'rejected': 'status-rejected',
            'cancelled': 'status-rejected',
            'completed': 'status-approved',
            'no_show': 'status-rejected'
        };
        return classMap[status] || 'status-pending';
    },

    // 获取今天的日期字符串
    getTodayString() {
        const today = new Date();
        return today.toISOString().split('T')[0];
    },

    // 获取明天的日期字符串
    getTomorrowString() {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        return tomorrow.toISOString().split('T')[0];
    },

    // 获取一周后的日期字符串
    getWeekLaterString() {
        const weekLater = new Date();
        weekLater.setDate(weekLater.getDate() + 7);
        return weekLater.toISOString().split('T')[0];
    },

    // 验证学号格式
    validateStudentId(studentId) {
        return /^\d{8,12}$/.test(studentId);
    },

    // 验证邮箱格式
    validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    },

    // 验证手机号格式
    validatePhone(phone) {
        return /^1[3-9]\d{9}$/.test(phone);
    },

    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 节流函数
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// 错误处理
window.addEventListener('unhandledrejection', event => {
    console.error('Unhandled promise rejection:', event.reason);
    showToast('系统错误，请稍后重试', 'error');
});

// 网络状态检测
window.addEventListener('online', () => {
    showToast('网络连接已恢复', 'success');
});

window.addEventListener('offline', () => {
    showToast('网络连接已断开', 'warning');
}); 