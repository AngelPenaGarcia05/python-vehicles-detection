// Configuración
const UPDATE_INTERVAL = 2000;
let aiEnabled = {{ 'true' if ai_enabled else 'false' }};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando dashboard...');
    initializeDashboard();
    setupEventListeners();
});

function initializeDashboard() {
    setInterval(updateMetrics, UPDATE_INTERVAL);
    updateMetrics(); // Primera actualización inmediata
    updateAIStatusDisplay();
}

function setupEventListeners() {
    // Botón de control IA
    const toggleAIButton = document.getElementById('toggleAI');
    if (toggleAIButton) {
        toggleAIButton.addEventListener('click', toggleAIAnalysis);
    }
}

function updateMetrics() {
    fetch('/metrics')
        .then(response => {
            if (!response.ok) throw new Error('Error en respuesta');
            return response.json();
        })
        .then(data => {
            console.log('📊 Datos recibidos:', data);
            updateGeneralMetrics(data);
            updateCameraCards(data.cameras);
            updateTrafficLights(data.traffic_lights, data.cameras);
            updateDetailedMetrics(data.cameras);
            updateLastUpdate();
            updateAIStatus(data.ai_enabled);
        })
        .catch(error => {
            console.error('❌ Error actualizando métricas:', error);
            showError('Error de conexión con el servidor');
        });
}

function updateGeneralMetrics(data) {
    // Total de vehículos
    const totalElement = document.getElementById('totalVehicles');
    if (totalElement) {
        totalElement.textContent = data.total_vehicles;
    }

    // Congestión general
    const congestionElement = document.getElementById('overallCongestion');
    const congestionCard = document.getElementById('congestionCard');
    
    if (congestionElement && congestionCard) {
        congestionElement.textContent = data.overall_congestion;
        
        // Actualizar color de la tarjeta
        congestionCard.className = `card text-white bg-${data.overall_congestion_badge}`;
    }
}

function updateCameraCards(cameras) {
    for (let camId = 0; camId < 4; camId++) {
        const camData = cameras[camId];
        
        if (!camData) continue;
        
        // Actualizar badge de estado
        const statusElement = document.getElementById(`cam${camId}-status`);
        if (statusElement) {
            statusElement.textContent = `${camData.count} vehículos`;
            statusElement.className = `badge bg-${camData.congestion_badge}`;
        }
        
        // Actualizar conteo
        const countElement = document.getElementById(`cam${camId}-count`);
        if (countElement) {
            countElement.textContent = camData.count;
        }
        
        // Actualizar congestión
        const congestionElement = document.getElementById(`cam${camId}-congestion`);
        if (congestionElement) {
            congestionElement.textContent = camData.congestion;
            congestionElement.className = `badge bg-${camData.congestion_badge}`;
        }
    }
}

function updateTrafficLights(lights, cameras) {
    // Actualizar luces Norte-Sur
    updateLightState('ns', lights.north_south);
    
    // Actualizar luces Este-Oeste
    updateLightState('ew', lights.east_west);
    
    // Actualizar conteos de tráfico
    const nsCount = (cameras[0]?.count || 0) + (cameras[2]?.count || 0);
    const ewCount = (cameras[1]?.count || 0) + (cameras[3]?.count || 0);
    
    const nsCountElement = document.getElementById('ns-count');
    const ewCountElement = document.getElementById('ew-count');
    
    if (nsCountElement) nsCountElement.textContent = `${nsCount} vehículos`;
    if (ewCountElement) ewCountElement.textContent = `${ewCount} vehículos`;
}

function updateLightState(direction, state) {
    const lights = ['red', 'yellow', 'green'];
    
    lights.forEach(light => {
        const element = document.getElementById(`${direction}-${light}`);
        if (element) {
            element.classList.toggle('active', light === state);
        }
    });
}

function updateDetailedMetrics(cameras) {
    const container = document.getElementById('detailedMetrics');
    if (!container) return;
    
    let html = '';
    
    for (let camId = 0; camId < 4; camId++) {
        const camData = cameras[camId];
        
        if (!camData) continue;
        
        html += `
            <div class="col-md-3 mb-3">
                <div class="card metric-card">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="fas fa-camera me-2"></i>Cámara ${camId + 1}
                        </h6>
                        <div class="row text-center">
                            <div class="col-6">
                                <div class="display-6 text-primary">${camData.count}</div>
                                <small class="text-muted">Vehículos</small>
                            </div>
                            <div class="col-6">
                                <span class="badge bg-${camData.congestion_badge} fs-6">
                                    ${camData.congestion}
                                </span>
                            </div>
                        </div>
                        ${Object.keys(camData.classes).length > 0 ? `
                            <div class="mt-3">
                                <small class="text-muted d-block mb-2">Distribución:</small>
                                ${Object.entries(camData.classes).map(([type, count]) => `
                                    <div class="d-flex justify-content-between small">
                                        <span>${type}:</span>
                                        <span class="fw-bold">${count}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : '<div class="mt-3 text-muted small">Sin vehículos detectados</div>'}
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function updateLastUpdate() {
    const element = document.getElementById('lastUpdate');
    if (element) {
        element.textContent = `Última actualización: ${new Date().toLocaleTimeString()}`;
    }
}

function updateAIStatus(status) {
    aiEnabled = status;
    updateAIStatusDisplay();
}

function updateAIStatusDisplay() {
    const statusElement = document.getElementById('aiStatus');
    const toggleButton = document.getElementById('toggleAI');
    
    if (statusElement) {
        statusElement.innerHTML = aiEnabled ? 
            '<span class="badge bg-success">IA ACTIVADA</span>' : 
            '<span class="badge bg-danger">IA DESACTIVADA</span>';
    }
    
    if (toggleButton) {
        toggleButton.innerHTML = aiEnabled ? 
            '<i class="fas fa-power-off me-2"></i>Desactivar IA' : 
            '<i class="fas fa-power-off me-2"></i>Activar IA';
        toggleButton.className = aiEnabled ? 'btn btn-warning' : 'btn btn-success';
    }
}

function toggleAIAnalysis() {
    fetch('/toggle_ai', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            aiEnabled = data.ai_enabled;
            updateAIStatusDisplay();
            showSuccess(data.message);
        } else {
            showError('Error al cambiar estado de IA');
        }
    })
    .catch(error => {
        console.error('❌ Error cambiando IA:', error);
        showError('Error de conexión');
    });
}

function showError(message) {
    showNotification(message, 'danger');
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showNotification(message, type) {
    // Eliminar notificaciones anteriores
    const existingAlerts = document.querySelectorAll('.status-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Crear nueva notificación
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show status-alert position-fixed`;
    alertDiv.style.cssText = 'top: 80px; right: 20px; z-index: 1050; min-width: 300px;';
    alertDiv.innerHTML = `
        <strong>${type === 'success' ? '✅' : '❌'} </strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-eliminar después de 3 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

// Forzar actualización manual
window.forceUpdate = function() {
    updateMetrics();
};