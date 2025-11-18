// Funciones JavaScript globales para la aplicación

// Inicializar tooltips de Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Función para formatear números
function formatNumber(num) {
    return new Intl.NumberFormat('es-ES').format(num);
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentElement) {
            alertDiv.remove();
        }
    }, 5000);
}

// Manejo de errores de fetch
function handleFetchError(error) {
    console.error('Error:', error);
    showNotification('Error de conexión. Por favor, intenta nuevamente.', 'error');
}

// Actualización automática de datos
function startAutoRefresh(interval = 5000) {
    setInterval(() => {
        if (window.location.pathname === '/dashboard' || window.location.pathname === '/') {
            fetch('/api/detection_data')
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                })
                .catch(handleFetchError);
        }
    }, interval);
}

// Función para actualizar el dashboard (puede ser extendida)
function updateDashboard(data) {
    // Actualizar contadores y estados aquí
    console.log('Datos actualizados:', data);
}

// Iniciar actualización automática cuando la página carga
document.addEventListener('DOMContentLoaded', function() {
    startAutoRefresh();
});