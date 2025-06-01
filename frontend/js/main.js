// 全局变量
let currentSection = 'home';
let courts = [];
let timeSlots = [];
let applications = [];
let reservations = [];

// 选中的时间段
let selectedSlots = [];

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    setupDateInput();
    initDateSelector();
    renderTimeSlots();
});

// 应用初始化
async function initializeApp() {
    try {
        // 加载场地信息
        await loadCourts();
        
        // 如果用户已登录，加载用户数据
        if (authManager.isLoggedIn()) {
            await loadUserData();
        }
        
        // 设置默认日期为明天
        const dateSelect = document.getElementById('date-select');
        if (dateSelect) {
            dateSelect.value = utils.getTomorrowString();
            dateSelect.min = utils.getTomorrowString();
            dateSelect.max = utils.getWeekLaterString();
        }
        
    } catch (error) {
        console.error('App initialization failed:', error);
        showToast('应用初始化失败，请刷新页面重试', 'error');
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 导航链接
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('href').substring(1);
            showSection(section);
        });
    });

    // 移动端导航切换
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
}

// 设置日期输入限制
function setupDateInput() {
    const dateSelect = document.getElementById('date-select');
    if (dateSelect) {
        // 限制只能选择明天到一周后的日期
        dateSelect.min = utils.getTomorrowString();
        dateSelect.max = utils.getWeekLaterString();
        
        // 监听日期变化
        dateSelect.addEventListener('change', () => {
            if (currentSection === 'booking') {
                loadTimeSlots();
            }
        });
    }
}

// 显示指定页面
function showSection(sectionId) {
    // 检查需要登录的页面
    const authRequiredSections = ['booking', 'status', 'profile'];
    if (authRequiredSections.includes(sectionId) && !authManager.isLoggedIn()) {
        showToast('请先登录', 'warning');
        openModal('login-modal');
        return;
    }

    // 隐藏所有页面
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    // 显示目标页面
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
        currentSection = sectionId;
        
        // 更新导航状态
        updateNavigation(sectionId);
        
        // 加载页面数据
        loadSectionData(sectionId);
    }
}

// 更新导航状态
function updateNavigation(activeSection) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${activeSection}`) {
            link.classList.add('active');
        }
    });
}

// 加载页面数据
async function loadSectionData(sectionId) {
    try {
        switch (sectionId) {
            case 'courts':
                await loadCourts();
                break;
            case 'booking':
                await loadTimeSlots();
                break;
            case 'status':
                await loadApplications();
                await loadReservations();
                break;
            case 'profile':
                await loadProfile();
                break;
        }
    } catch (error) {
        console.error(`Failed to load ${sectionId} data:`, error);
        showToast('数据加载失败，请稍后重试', 'error');
    }
}

// 加载用户数据
async function loadUserData() {
    try {
        await Promise.all([
            loadApplications(),
            loadReservations(),
            loadProfile()
        ]);
    } catch (error) {
        console.error('Failed to load user data:', error);
    }
}

// 加载场地信息
async function loadCourts() {
    try {
        showLoading('courts-grid');
        const response = await api.getCourts();
        courts = response.courts || [];
        renderCourts();
        updateCourtFilter();
    } catch (error) {
        console.error('Failed to load courts:', error);
        showError('courts-grid', '加载场地信息失败');
    }
}

// 渲染场地列表
function renderCourts() {
    const container = document.getElementById('courts-grid');
    if (!container) return;

    if (courts.length === 0) {
        showEmpty(container, '暂无场地信息');
        return;
    }

    container.innerHTML = courts.map(court => `
        <div class="court-card">
            <h3>${court.name}</h3>
            <p>${court.description || '暂无描述'}</p>
            <div class="court-info">
                <div class="info-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <span>${court.location || '位置待定'}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-users"></i>
                    <span>容量: ${court.capacity || '未知'}</span>
                </div>
                <div class="info-item">
                    <i class="fas fa-tag"></i>
                    <span>类型: ${court.type || '通用'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// 更新场地筛选器
function updateCourtFilter() {
    const select = document.getElementById('court-filter');
    if (!select) return;

    select.innerHTML = '<option value="">全部场地</option>' +
        courts.map(court => `<option value="${court.id}">${court.name}</option>`).join('');
}

// 加载时间段
async function loadTimeSlots() {
    const dateSelect = document.getElementById('date-select');
    const courtFilter = document.getElementById('court-filter');
    
    if (!dateSelect || !dateSelect.value) {
        showToast('请选择日期', 'warning');
        return;
    }

    try {
        showLoading('timeslots-grid');
        
        const date = dateSelect.value;
        const courtId = courtFilter ? courtFilter.value : null;
        
        const response = await api.getAvailableTimeSlots(date, courtId);
        timeSlots = response.timeslots || [];
        renderTimeSlots();
    } catch (error) {
        console.error('Failed to load timeslots:', error);
        showError('timeslots-grid', '加载时间段失败');
    }
}

// 初始化日期选择
function initDateSelector() {
    const dateSelector = document.querySelector('.date-selector');
    if (!dateSelector) return;

    // 清空现有按钮
    dateSelector.innerHTML = '';

    // 生成未来7天的日期按钮
    for (let i = 0; i < 7; i++) {
        const date = new Date();
        date.setDate(date.getDate() + i);
        
        const btn = document.createElement('button');
        btn.className = 'date-btn' + (i === 0 ? ' active' : '');
        btn.setAttribute('data-date', formatDate(date));
        btn.textContent = formatDateShort(date);
        
        btn.addEventListener('click', () => {
            document.querySelectorAll('.date-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedSlots = [];
            renderTimeSlots();
        });
        
        dateSelector.appendChild(btn);
    }
}

// 格式化日期 YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().split('T')[0];
}

// 格式化短日期 MM-DD
function formatDateShort(date) {
    return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}

// 渲染时间段列表
function renderTimeSlots() {
    const container = document.getElementById('timeslots-grid');
    if (!container) return;

    if (timeSlots.length === 0) {
        showEmpty(container, '当前日期暂无可用时间段');
        return;
    }

    // 按时间段分组
    const timeGroups = {};
    timeSlots.forEach(slot => {
        const timeKey = `${utils.formatTime(slot.start_time)} - ${utils.formatTime(slot.end_time)}`;
        if (!timeGroups[timeKey]) {
            timeGroups[timeKey] = [];
        }
        timeGroups[timeKey].push(slot);
    });

    // 生成场地表头
    const courtsHeader = document.createElement('div');
    courtsHeader.className = 'courts-header';
    courtsHeader.innerHTML = `
        <div class="court-header-item">时间</div>
        ${courts.slice(0, 4).map(court => `
            <div class="court-header-item">
                ${court.name.replace('羽毛球场', '')}号场
            </div>
        `).join('')}
    `;

    // 生成时间段行
    const timeSlotsContent = document.createElement('div');
    timeSlotsContent.className = 'timeslots-grid';
    timeSlotsContent.innerHTML = Object.entries(timeGroups)
        .sort(([timeA], [timeB]) => timeA.localeCompare(timeB))
        .map(([time, slots]) => {
            return `
                <div class="timeslot-row">
                    <div class="timeslot-time">
                        ${time}
                    </div>
                    ${courts.slice(0, 4).map(court => {
                        const slot = slots.find(s => s.court_id === court.id);
                        if (!slot) return `
                            <div class="timeslot-card">
                                <div class="timeslot-status">不可预约</div>
                            </div>
                        `;

                        const statusClass = getTimeSlotStatusClass(slot.status);
                        const statusText = getTimeSlotStatusText(slot.status);
                        
                        return `
                            <div class="timeslot-card ${statusClass}" onclick="handleTimeSlotClick(${slot.id})">
                                <div class="timeslot-status status-${slot.status}">
                                    ${statusText}
                                </div>
                                ${slot.applications_count ? `
                                    <div class="timeslot-info">
                                        <div><i class="fas fa-users"></i> ${slot.applications_count} 人申请</div>
                                    </div>
                                ` : ''}
                                ${slot.status === 'available' ? `
                                    <button class="btn btn-primary btn-full" onclick="event.stopPropagation(); applyForTimeSlot(${slot.id})">
                                        申请
                                    </button>
                                ` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }).join('');

    // 清空并添加新内容
    container.innerHTML = '';
    container.appendChild(courtsHeader);
    container.appendChild(timeSlotsContent);
}

// 获取时间段状态CSS类
function getTimeSlotStatusClass(status) {
    const classMap = {
        'available': 'available',
        'has_applications': 'pending',
        'reserved': 'reserved'
    };
    return classMap[status] || 'available';
}

// 获取时间段状态文本
function getTimeSlotStatusText(status) {
    const textMap = {
        'available': '可申请',
        'has_applications': '有申请',
        'reserved': '已预约'
    };
    return textMap[status] || status;
}

// 切换时间段选择状态
function toggleSlotSelection(cell, slotData) {
    const isSelected = cell.classList.contains('selected');
    
    if (isSelected) {
        cell.classList.remove('selected');
        selectedSlots = selectedSlots.filter(slot => 
            !(slot.time === slotData.time && slot.courtId === slotData.courtId)
        );
    } else {
        cell.classList.add('selected');
        selectedSlots.push(slotData);
    }
    
    updateSelectedSlots();
}

// 更新选中的时间段显示
function updateSelectedSlots() {
    const container = document.getElementById('selected-slots');
    const totalPriceElement = document.querySelector('.total-price');
    let totalPrice = 0;
    
    // 按场地分组
    const groupedSlots = {};
    selectedSlots.forEach(slot => {
        const courtId = slot.courtId;
        if (!groupedSlots[courtId]) {
            groupedSlots[courtId] = [];
        }
        groupedSlots[courtId].push(slot);
        totalPrice += slot.price;
    });
    
    // 渲染选中的时间段
    container.innerHTML = Object.entries(groupedSlots).map(([courtId, slots]) => `
        <div class="selected-slot-card">
            <div class="selected-slot-venue">羽毛球场${courtId}号</div>
            ${slots.map(slot => `
                <div class="selected-slot-time">
                    <span>${slot.time}</span>
                    <span class="selected-slot-price">¥${slot.price.toFixed(2)}</span>
                </div>
            `).join('')}
            <div class="selected-slot-date">${getCurrentDate()} 共${slots.length}场</div>
        </div>
    `).join('');
    
    // 更新总价
    totalPriceElement.textContent = `¥${totalPrice.toFixed(2)}`;
}

// 获取当前选择的日期
function getCurrentDate() {
    const activeDate = document.querySelector('.date-btn.active');
    return activeDate ? activeDate.dataset.date : '2025-05-26';
}

function getStatusText(status) {
    switch(status) {
        case 'available':
            return '可申请';
        case 'pending':
            return '有申请';
        case 'reserved':
            return '已预约';
        default:
            return '可申请';
    }
}

// 处理时间段点击
function handleTimeSlotClick(slotId) {
    const slot = timeSlots.find(s => s.id === slotId);
    if (!slot) return;

    if (slot.status === 'available') {
        applyForTimeSlot(slotId);
    } else {
        showToast(`该时间段${getStatusText(slot.status)}`, 'info');
    }
}

// 申请时间段
async function applyForTimeSlot(slotId) {
    if (!authManager.requireAuth()) return;

    try {
        const slot = timeSlots.find(s => s.id === slotId);
        if (!slot) {
            showToast('时间段信息不存在', 'error');
            return;
        }

        const confirmed = confirm(`确认申请预约？\n时间：${utils.formatTime(slot.start_time)} - ${utils.formatTime(slot.end_time)}\n日期：${utils.formatDate(slot.date)}`);
        if (!confirmed) return;

        await api.submitApplication({ timeslot_id: slotId });
        showToast('申请提交成功！', 'success');
        
        // 刷新时间段列表
        await loadTimeSlots();
        
        // 刷新申请状态
        if (currentSection === 'status') {
            await loadApplications();
        }
    } catch (error) {
        console.error('Failed to apply for timeslot:', error);
        showToast(error.message || '申请失败，请稍后重试', 'error');
    }
}

// 加载申请列表
async function loadApplications() {
    if (!authManager.isLoggedIn()) return;

    try {
        const response = await api.getStudentStatus();
        applications = response.applications || [];
        renderApplications();
    } catch (error) {
        console.error('Failed to load applications:', error);
        showError('applications-list', '加载申请列表失败');
    }
}

// 渲染申请列表
function renderApplications() {
    const container = document.getElementById('applications-list');
    if (!container) return;

    if (applications.length === 0) {
        showEmpty(container, '暂无申请记录');
        return;
    }

    container.innerHTML = applications.map(app => {
        const court = courts.find(c => c.id === app.court_id);
        return `
            <div class="application-card">
                <div class="card-header">
                    <span class="card-title">${court ? court.name : '未知场地'}</span>
                    <span class="card-status ${utils.getStatusClass(app.status)}">${utils.getStatusText(app.status)}</span>
                </div>
                <div class="card-info">
                    <div class="info-group">
                        <span class="info-label">日期</span>
                        <span class="info-value">${utils.formatDate(app.date)}</span>
                    </div>
                    <div class="info-group">
                        <span class="info-label">时间</span>
                        <span class="info-value">${utils.formatTime(app.start_time)} - ${utils.formatTime(app.end_time)}</span>
                    </div>
                    <div class="info-group">
                        <span class="info-label">申请时间</span>
                        <span class="info-value">${utils.formatDateTime(app.created_at)}</span>
                    </div>
                    <div class="info-group">
                        <span class="info-label">优先级权重</span>
                        <span class="info-value">${app.priority_weight ? app.priority_weight.toFixed(3) : 'N/A'}</span>
                    </div>
                </div>
                ${app.status === 'pending' ? `
                    <div class="card-actions">
                        <button class="btn btn-danger" onclick="cancelApplication(${app.id})">
                            <i class="fas fa-times"></i>
                            取消申请
                        </button>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// 取消申请
async function cancelApplication(applicationId) {
    try {
        const confirmed = confirm('确认取消申请？');
        if (!confirmed) return;

        const app = applications.find(a => a.id === applicationId);
        if (!app) {
            showToast('申请信息不存在', 'error');
            return;
        }

        await api.cancelApplication({ 
            timeslot_id: app.timeslot_id 
        });
        
        showToast('申请已取消', 'success');
        
        // 刷新申请列表
        await loadApplications();
        
        // 如果在预约页面，也刷新时间段
        if (currentSection === 'booking') {
            await loadTimeSlots();
        }
    } catch (error) {
        console.error('Failed to cancel application:', error);
        showToast(error.message || '取消申请失败', 'error');
    }
}

// 加载预约记录
async function loadReservations() {
    if (!authManager.isLoggedIn()) return;

    try {
        const response = await api.getStudentRecords();
        reservations = response.records || [];
        renderReservations();
    } catch (error) {
        console.error('Failed to load reservations:', error);
        showError('reservations-list', '加载预约记录失败');
    }
}

// 渲染预约记录
function renderReservations() {
    const container = document.getElementById('reservations-list');
    if (!container) return;

    if (reservations.length === 0) {
        showEmpty(container, '暂无预约记录');
        return;
    }

    container.innerHTML = reservations.map(record => {
        const court = courts.find(c => c.id === record.court_id);
        return `
            <div class="reservation-card">
                <div class="card-header">
                    <span class="card-title">${court ? court.name : '未知场地'}</span>
                    <span class="card-status ${utils.getStatusClass(record.status)}">${utils.getStatusText(record.status)}</span>
                </div>
                <div class="card-info">
                    <div class="info-group">
                        <span class="info-label">日期</span>
                        <span class="info-value">${utils.formatDate(record.date)}</span>
                    </div>
                    <div class="info-group">
                        <span class="info-label">时间</span>
                        <span class="info-value">${utils.formatTime(record.start_time)} - ${utils.formatTime(record.end_time)}</span>
                    </div>
                    <div class="info-group">
                        <span class="info-label">预约时间</span>
                        <span class="info-value">${utils.formatDateTime(record.created_at)}</span>
                    </div>
                    ${record.completed_at ? `
                        <div class="info-group">
                            <span class="info-label">完成时间</span>
                            <span class="info-value">${utils.formatDateTime(record.completed_at)}</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

// 加载个人资料
async function loadProfile() {
    if (!authManager.isLoggedIn()) return;

    try {
        const [creditResponse, recordsResponse] = await Promise.all([
            api.getStudentCredit(),
            api.getStudentRecords()
        ]);
        
        renderProfile(creditResponse, recordsResponse);
    } catch (error) {
        console.error('Failed to load profile:', error);
        showError('profile-info', '加载个人信息失败');
    }
}

// 渲染个人资料
function renderProfile(creditData, recordsData) {
    const user = authManager.getCurrentUser();
    if (!user) return;

    // 基本信息
    const profileInfo = document.getElementById('profile-info');
    if (profileInfo) {
        profileInfo.innerHTML = `
            <div class="info-group">
                <span class="info-label">学号</span>
                <span class="info-value">${user.student_id}</span>
            </div>
            <div class="info-group">
                <span class="info-label">姓名</span>
                <span class="info-value">${user.name}</span>
            </div>
            <div class="info-group">
                <span class="info-label">邮箱</span>
                <span class="info-value">${user.email}</span>
            </div>
            ${user.phone ? `
                <div class="info-group">
                    <span class="info-label">手机号</span>
                    <span class="info-value">${user.phone}</span>
                </div>
            ` : ''}
            <div class="info-group">
                <span class="info-label">注册时间</span>
                <span class="info-value">${utils.formatDateTime(user.created_at)}</span>
            </div>
        `;
    }

    // 信用评分
    const creditScore = document.getElementById('credit-score');
    if (creditScore && creditData) {
        const score = creditData.credit_score || 100;
        creditScore.innerHTML = `
            <div class="credit-number">${score}</div>
            <div class="credit-label">信用评分</div>
            <div class="credit-bar">
                <div class="credit-fill" style="width: ${score}%"></div>
            </div>
            <div class="credit-description">
                ${score >= 90 ? '信用优秀' : score >= 70 ? '信用良好' : score >= 50 ? '信用一般' : '信用较差'}
            </div>
        `;
    }

    // 统计信息
    const statsGrid = document.getElementById('stats-grid');
    if (statsGrid && recordsData) {
        const records = recordsData.records || [];
        const completedCount = records.filter(r => r.status === 'completed').length;
        const noShowCount = records.filter(r => r.status === 'no_show').length;
        const totalCount = records.length;
        const successRate = totalCount > 0 ? ((completedCount / totalCount) * 100).toFixed(1) : '0.0';

        statsGrid.innerHTML = `
            <div class="stat-item">
                <div class="stat-number">${totalCount}</div>
                <div class="stat-label">总预约次数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${completedCount}</div>
                <div class="stat-label">成功使用</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${noShowCount}</div>
                <div class="stat-label">爽约次数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${successRate}%</div>
                <div class="stat-label">使用率</div>
            </div>
        `;
    }
}

// 状态标签页切换
function showStatusTab(tabName) {
    // 更新标签按钮状态
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // 显示对应内容
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    const targetTab = document.getElementById(`${tabName}-tab`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
}

// 工具函数
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
            </div>
        `;
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>加载失败</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

function showEmpty(container, message) {
    if (typeof container === 'string') {
        container = document.getElementById(container);
    }
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <h3>暂无数据</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// 全局函数（供HTML调用）
window.showSection = showSection;
window.loadTimeSlots = loadTimeSlots;
window.showStatusTab = showStatusTab;
window.applyForTimeSlot = applyForTimeSlot;
window.cancelApplication = cancelApplication; 