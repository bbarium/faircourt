// 认证管理类
class AuthManager {
    constructor() {
        this.currentUser = null;
        this.init();
    }

    // 初始化认证状态
    init() {
        const token = localStorage.getItem('token');
        const userData = localStorage.getItem('userData');
        
        if (token && userData) {
            try {
                this.currentUser = JSON.parse(userData);
                this.updateUIForLoggedInUser();
            } catch (error) {
                console.error('Failed to parse user data:', error);
                this.logout();
            }
        } else {
            this.updateUIForLoggedOutUser();
        }
    }

    // 登录
    async login(studentId, password) {
        try {
            const response = await api.loginStudent({
                student_id: studentId,
                password: password
            });

            if (response.token) {
                this.currentUser = response.student;
                localStorage.setItem('userData', JSON.stringify(this.currentUser));
                this.updateUIForLoggedInUser();
                showToast('登录成功！', 'success');
                closeModal('login-modal');
                return true;
            }
        } catch (error) {
            console.error('Login failed:', error);
            showToast(error.message || '登录失败，请检查学号和密码', 'error');
            return false;
        }
    }

    // 注册
    async register(formData) {
        try {
            // 验证表单数据
            if (!this.validateRegistrationData(formData)) {
                return false;
            }

            const response = await api.registerStudent(formData);
            showToast('注册成功！请登录', 'success');
            closeModal('register-modal');
            openModal('login-modal');
            return true;
        } catch (error) {
            console.error('Registration failed:', error);
            showToast(error.message || '注册失败，请稍后重试', 'error');
            return false;
        }
    }

    // 退出登录
    logout() {
        this.currentUser = null;
        localStorage.removeItem('token');
        localStorage.removeItem('userData');
        api.logout();
        this.updateUIForLoggedOutUser();
        showToast('已退出登录', 'success');
        showSection('home');
    }

    // 验证注册数据
    validateRegistrationData(data) {
        if (!utils.validateStudentId(data.student_id)) {
            showToast('请输入有效的学号（8-12位数字）', 'error');
            return false;
        }

        if (!data.name || data.name.trim().length < 2) {
            showToast('请输入有效的姓名', 'error');
            return false;
        }

        if (!utils.validateEmail(data.email)) {
            showToast('请输入有效的邮箱地址', 'error');
            return false;
        }

        if (data.phone && !utils.validatePhone(data.phone)) {
            showToast('请输入有效的手机号码', 'error');
            return false;
        }

        if (!data.password || data.password.length < 6) {
            showToast('密码长度至少6位', 'error');
            return false;
        }

        if (data.password !== data.confirm_password) {
            showToast('两次输入的密码不一致', 'error');
            return false;
        }

        return true;
    }

    // 更新已登录用户的UI
    updateUIForLoggedInUser() {
        const loginBtn = document.getElementById('login-btn');
        const registerBtn = document.getElementById('register-btn');
        const userMenu = document.getElementById('user-menu');
        const userName = document.getElementById('user-name');

        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        if (userMenu) userMenu.style.display = 'flex';
        if (userName && this.currentUser) {
            userName.textContent = this.currentUser.name;
        }
    }

    // 更新未登录用户的UI
    updateUIForLoggedOutUser() {
        const loginBtn = document.getElementById('login-btn');
        const registerBtn = document.getElementById('register-btn');
        const userMenu = document.getElementById('user-menu');

        if (loginBtn) loginBtn.style.display = 'inline-flex';
        if (registerBtn) registerBtn.style.display = 'inline-flex';
        if (userMenu) userMenu.style.display = 'none';
    }

    // 检查是否已登录
    isLoggedIn() {
        return this.currentUser !== null;
    }

    // 获取当前用户
    getCurrentUser() {
        return this.currentUser;
    }

    // 需要登录的操作检查
    requireAuth(callback) {
        if (!this.isLoggedIn()) {
            showToast('请先登录', 'warning');
            openModal('login-modal');
            return false;
        }
        if (callback) callback();
        return true;
    }
}

// 创建全局认证管理器实例
const authManager = new AuthManager();

// 模态框管理
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
    }
}

// 消息提示
function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const toastId = Date.now();
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${getToastTitle(type)}</span>
            <span class="toast-close" onclick="removeToast(${toastId})">&times;</span>
        </div>
        <div class="toast-message">${message}</div>
    `;
    
    toast.id = `toast-${toastId}`;
    container.appendChild(toast);

    // 自动移除
    setTimeout(() => {
        removeToast(toastId);
    }, duration);
}

function getToastTitle(type) {
    const titles = {
        success: '成功',
        error: '错误',
        warning: '警告',
        info: '提示'
    };
    return titles[type] || '提示';
}

function removeToast(toastId) {
    const toast = document.getElementById(`toast-${toastId}`);
    if (toast) {
        toast.style.animation = 'toastSlideOut 0.3s ease forwards';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }
}

// 事件监听器
document.addEventListener('DOMContentLoaded', function() {
    // 登录按钮
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => openModal('login-modal'));
    }

    // 注册按钮
    const registerBtn = document.getElementById('register-btn');
    if (registerBtn) {
        registerBtn.addEventListener('click', () => openModal('register-modal'));
    }

    // 退出按钮
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => authManager.logout());
    }

    // 登录表单
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const studentId = document.getElementById('login-student-id').value;
            const password = document.getElementById('login-password').value;
            
            if (!studentId || !password) {
                showToast('请填写完整的登录信息', 'error');
                return;
            }

            await authManager.login(studentId, password);
        });
    }

    // 注册表单
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = {
                student_id: document.getElementById('register-student-id').value,
                name: document.getElementById('register-name').value,
                email: document.getElementById('register-email').value,
                phone: document.getElementById('register-phone').value,
                password: document.getElementById('register-password').value,
                confirm_password: document.getElementById('register-confirm-password').value
            };

            await authManager.register(formData);
        });
    }

    // 模态框点击外部关闭
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('show');
            e.target.style.display = 'none';
        }
    });

    // ESC键关闭模态框
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                modal.classList.remove('show');
                modal.style.display = 'none';
            });
        }
    });
});

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes toastSlideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style); 