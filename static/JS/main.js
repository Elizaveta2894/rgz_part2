document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
    initCopyButtons();
    initForms();
});

function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', showTooltip);
        el.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const tooltipText = this.getAttribute('data-tooltip');
    if (!tooltipText) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.position = 'absolute';
    tooltip.style.background = 'rgba(0,0,0,0.8)';
    tooltip.style.color = 'white';
    tooltip.style.padding = '5px 10px';
    tooltip.style.borderRadius = '3px';
    tooltip.style.fontSize = '12px';
    tooltip.style.zIndex = '1000';
    
    document.body.appendChild(tooltip);
    
    const rect = this.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
    
    this._tooltip = tooltip;
}

function hideTooltip(e) {
    if (this._tooltip) {
        this._tooltip.remove();
        delete this._tooltip;
    }
}

function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(btn => {
        btn.addEventListener('click', copyToClipboard);
    });
}

async function copyToClipboard(e) {
    const text = this.getAttribute('data-copy') || this.previousElementSibling?.textContent;
    if (!text) return;
    
    try {
        await navigator.clipboard.writeText(text);
        showNotification('Текст скопирован в буфер обмена!', 'success');
    } catch (err) {
        console.error('Ошибка копирования:', err);
        showNotification('Не удалось скопировать текст', 'error');
    }
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

function initForms() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', validateForm);
    });
}

function validateForm(e) {
    const form = e.target;
    const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showInputError(input, 'Это поле обязательно для заполнения');
            isValid = false;
        } else {
            clearInputError(input);
            
            // Специфичная валидация
            if (input.type === 'email' && !isValidEmail(input.value)) {
                showInputError(input, 'Введите корректный email');
                isValid = false;
            }
            
            if (input.type === 'password' && input.value.length < 6) {
                showInputError(input, 'Пароль должен быть не менее 6 символов');
                isValid = false;
            }
        }
    });
    
    if (!isValid) {
        e.preventDefault();
        showNotification('Пожалуйста, исправьте ошибки в форме', 'error');
    }
}

function showInputError(input, message) {
    clearInputError(input);
    input.classList.add('error');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'input-error';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #f44336;
        font-size: 12px;
        margin-top: 5px;
    `;
    
    input.parentNode.appendChild(errorDiv);
}

function clearInputError(input) {
    input.classList.remove('error');
    const existingError = input.parentNode.querySelector('.input-error');
    if (existingError) {
        existingError.remove();
    }
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

async function callJsonRpc(method, params = {}) {
    try {
        const response = await fetch('/api', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: method,
                params: params,
                id: Date.now()
            })
        });
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

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

function formatTime(minutes) {
    if (minutes < 60) {
        return `${minutes} мин`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}ч ${mins}мин` : `${hours}ч`;
}
window.App = {
    callJsonRpc,
    showNotification,
    formatTime,
    debounce
};

// Динамическая загрузка статистики
async function loadStats() {
    try {
        // Показываем состояние загрузки
        const statElements = [
            'stat-users', 'stat-total-time', 'stat-categories',
            'most-popular', 'avg-time', 'total-views'
        ];
        
        statElements.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '...';
        });

        // 1. Загружаем общую статистику
        const statsResponse = await App.callJsonRpc('get_recipes_count', {});
        
        if (statsResponse.result) {
            const stats = statsResponse.result;
            
            // Обновляем основные показатели
            document.getElementById('stat-users').textContent = 2; // Ваши 2 пользователя
            document.getElementById('stat-total-time').textContent = 
                Math.round(stats.avg_cooking_time * stats.total);
            document.getElementById('stat-categories').textContent = 
                Object.keys(stats.categories).length;
            document.getElementById('avg-time').innerHTML = 
                `${Math.round(stats.avg_cooking_time)} <span style="font-size: 0.8em">мин</span>`;
            document.getElementById('total-views').textContent = 
                stats.total_views.toLocaleString();
            
            // 2. Загружаем самый популярный рецепт
            const popularResponse = await App.callJsonRpc('get_popular_recipes', { count: 1 });
            if (popularResponse.result?.recipes?.length > 0) {
                const recipe = popularResponse.result.recipes[0];
                document.getElementById('most-popular').textContent = recipe.title;
                document.getElementById('most-popular-views').textContent = 
                    `(${recipe.views} просмотров)`;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        // Можно показать значения по умолчанию или сообщение об ошибке
        document.getElementById('most-popular').textContent = 'Не удалось загрузить';
        App.showNotification('Статистика обновляется...', 'info');
    }
}

// Запускаем загрузку статистики при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Ваши существующие инициализации
    initTooltips();
    initCopyButtons();
    initForms();
    
    // Загружаем статистику только если на странице есть блок статистики
    if (document.querySelector('.stats-section')) {
        loadStats();
    }
});