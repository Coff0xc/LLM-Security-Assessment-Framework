/**
 * FORGEDAN Web 界面 JavaScript
 * 通用功能和 API 交互
 */

// API 基础配置
const API_BASE = '';

/**
 * 通用 API 请求函数
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}/api${endpoint}`;
    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };
    
    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * 加载仪表盘统计
 */
async function loadDashboardStats() {
    try {
        // 从本地存储加载统计
        const stats = JSON.parse(localStorage.getItem('forgedan_stats') || '{}');
        
        document.getElementById('total-tests').textContent = stats.total || 0;
        document.getElementById('success-count').textContent = stats.success || 0;
        document.getElementById('blocked-count').textContent = stats.blocked || 0;
        
        const total = stats.total || 0;
        const blocked = stats.blocked || 0;
        const rate = total > 0 ? ((blocked / total) * 100).toFixed(1) : 0;
        document.getElementById('safety-rate').textContent = `${rate}%`;
        
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

/**
 * 加载最近测试
 */
async function loadRecentTests() {
    try {
        const reports = await apiRequest('/reports');
        const tbody = document.getElementById('recent-tests-body');
        
        if (reports.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">暂无测试记录</td></tr>';
            return;
        }
        
        tbody.innerHTML = reports.slice(0, 5).map(report => `
            <tr>
                <td>${formatDate(report.created)}</td>
                <td>${report.name}</td>
                <td>-</td>
                <td><span class="status-badge completed">完成</span></td>
                <td>
                    <a href="/api/reports/${report.name}" target="_blank" class="btn btn-small">
                        查看
                    </a>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('加载最近测试失败:', error);
    }
}

/**
 * 更新统计数据
 */
function updateStats(success, blocked) {
    const stats = JSON.parse(localStorage.getItem('forgedan_stats') || '{"total":0,"success":0,"blocked":0}');
    stats.total++;
    if (success) {
        stats.success++;
    } else {
        stats.blocked++;
    }
    localStorage.setItem('forgedan_stats', JSON.stringify(stats));
}

/**
 * 格式化日期
 */
function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 格式化文件大小
 */
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-message">${message}</span>
        <button class="notification-close">&times;</button>
    `;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 自动消失
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
    
    // 点击关闭
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
}

/**
 * 复制到剪贴板
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板', 'success');
    } catch (error) {
        showNotification('复制失败', 'error');
    }
}

/**
 * 确认对话框
 */
function confirmAction(message) {
    return new Promise((resolve) => {
        resolve(window.confirm(message));
    });
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 导出函数供其他模块使用
window.forgedan = {
    apiRequest,
    loadDashboardStats,
    loadRecentTests,
    updateStats,
    formatDate,
    formatSize,
    showNotification,
    copyToClipboard,
    confirmAction,
    debounce,
    throttle
};
