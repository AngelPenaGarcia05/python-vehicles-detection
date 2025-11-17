// Configuración
const UPDATE_INTERVAL = 2000; // 2 segundos
const TRAFFIC_LIGHT_UPDATE_INTERVAL = 1000; // 1 segundo

// Estado de la aplicación
let appState = {
    isInitialized: false,
    lastUpdate: null,
    errorCount: 0
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando aplicación de monitoreo de tráfico...');
    initializeApp();
});

function initializeApp() {
    // Iniciar actualizaciones periódicas
    setInterval(updateMetrics, UPDATE_INTERVAL);
    setInterval(updateTrafficLights, TRAFFIC_LIGHT_UPDATE_INTERVAL);
    
    // Primera actualización inmediata
    updateMetrics();
    updateTrafficLights();
    
    appState.isInitialized = true;
    appState.lastUpdate = new Date();
    
    console.log('✅ Aplicación inicializada correctamente');
    
    // Mostrar estado inicial
    showStatus('Sistema conectado', 'success');
}

function updateMetrics() {
    fetch('/metrics')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📊 Datos recibidos:', data);
            
            updateGeneralMetrics(data);
            updateCameraMetrics(data.cameras);
            updateDetailedMetrics(data.cameras);
            updateTrafficCounts(data.cameras);
            
            // Actualizar timestamp
            const now = new Date();
            document.getElementById('lastUpdate').textContent = 
                `Última actualización: ${now.toLocaleTimeString()}`;
            
            appState.lastUpdate = now;
            appState.errorCount = 0;
            
        })
        .catch(error => {
            console.error('❌ Error al obtener métricas:', error);
            appState.errorCount++;
            
            if (appState.errorCount > 3) {
                showError('Error de conexión persistente con el servidor');
            }
        });
}

function updateGeneralMetrics(data) {
    // Actualizar vehículos totales
    const totalVehiclesElement = document.getElementById('totalVehicles');
    if (totalVehiclesElement) {
        totalVehiclesElement.textContent = data.total_vehicles;
        console.log(`🚗 Total vehículos actualizado: ${data.total_vehicles}`);
    }
    
    // Actualizar congestión general
    const overallCongestionElement = document.getElementById('overallCongestion');
    if (overallCongestionElement) {
        overallCongestionElement.textContent = data.overall_congestion;
        
        // Actualizar color de la tarjeta
        const cardElement = overallCongestionElement.closest('.card');
        if (cardElement) {
            // Remover clases anteriores
            cardElement.classList.remove('bg-success', 'bg-warning', 'bg-danger');
            // Añadir nueva clase
            cardElement.classList.add(`bg-${data.overall_congestion_badge}`);
        }
        
        console.log(`📈 Congestión general: ${data.overall_congestion}`);
    }
}

function updateTrafficCounts(cameras) {
    // Actualizar conteos para direcciones de semáforos
    const nsCount = (cameras[0]?.count || 0) + (cameras[2]?.count || 0);
    const ewCount = (cameras[1]?.count || 0) + (cameras[3]?.count || 0);
    
    const nsElement = document.getElementById('ns-count');
    const ewElement = document.getElementById('ew-count');
    
    if (nsElement) nsElement.textContent = `${nsCount} vehículos`;
    if (ewElement) ewElement.textContent = `${ewCount} vehículos`;
    
    console.log(`🛣️  Conteos: N-S ${nsCount}, E-W ${ewCount}`);
}

function updateCameraMetrics(cameras) {
    for (let camId = 0; camId < 4; camId++) {
        const camData = cameras[camId];
        const statusElement = document.getElementById(`cam${camId}-status`);
        const metricsElement = document.getElementById(`cam${camId}-metrics`);
        
        if (statusElement && metricsElement) {
            if (camData && camData.count !== undefined) {
                // Actualizar badge de estado
                statusElement.textContent = `${camData.count} vehículos`;
                statusElement.className = `badge bg-${camData.congestion_badge} camera-status`;
                
                // Actualizar métricas en el footer
                let metricsText = `Congestión: ${camData.congestion}`;
                if (camData.classes && Object.keys(camData.classes).length > 0) {
                    const classDetails = Object.entries(camData.classes)
                        .map(([cls, count]) => `${cls}: ${count}`)
                        .join(', ');
                    metricsText += ` | ${classDetails}`;
                }
                
                metricsElement.textContent = metricsText;
                
                console.log(`📷 Cámara ${camId + 1}: ${camData.count} vehículos`);
                
            } else {
                // Datos no disponibles
                statusElement.textContent = 'Sin datos';
                statusElement.className = 'badge bg-secondary camera-status';
                metricsElement.textContent = 'Esperando datos del servidor...';
            }
        }
    }
}

function updateDetailedMetrics(cameras) {
    const container = document.getElementById('detailedMetrics');
    if (!container) return;
    
    let html = '';
    
    for (let camId = 0; camId < 4; camId++) {
        const camData = cameras[camId];
        const vehicleCount = camData ? camData.count : 0;
        const congestionLevel = camData ? camData.congestion : 'N/A';
        const congestionBadge = camData ? camData.congestion_badge : 'secondary';
        const classes = camData ? camData.classes : {};
        
        html += `
            <div class="col-md-3 mb-3">
                <div class="metric-card">
                    <h6><i class="fas fa-video me-1"></i>Cámara ${camId + 1}</h6>
                    <div class="count">${vehicleCount}</div>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-${congestionBadge}">
                            <i class="fas fa-traffic-light me-1"></i>${congestionLevel}
                        </small>
                        <span class="badge bg-${congestionBadge}">${vehicleCount} vehículos</span>
                    </div>
                    ${Object.keys(classes).length > 0 ? `
                        <div class="mt-2 pt-2 border-top">
                            <small class="text-muted d-block mb-1">Distribución:</small>
                            ${Object.entries(classes)
                                .map(([cls, count]) => 
                                    `<span class="badge bg-light text-dark me-1 mb-1">${cls}: ${count}</span>`
                                ).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function updateTrafficLights() {
    fetch('/metrics')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateLightState('ns', data.traffic_lights.north_south);
            updateLightState('ew', data.traffic_lights.east_west);
            
            console.log(`🚦 Semáforos: N-S ${data.traffic_lights.north_south}, E-W ${data.traffic_lights.east_west}`);
        })
        .catch(error => {
            console.error('Error al obtener estado de semáforos:', error);
        });
}

function updateLightState(direction, state) {
    const redLight = document.getElementById(`${direction}-red`);
    const yellowLight = document.getElementById(`${direction}-yellow`);
    const greenLight = document.getElementById(`${direction}-green`);
    
    // Remover estado activo de todas las luces
    [redLight, yellowLight, greenLight].forEach(light => {
        if (light) {
            light.classList.remove('active');
        }
    });
    
    // Activar la luz correspondiente
    switch (state) {
        case 'red':
            if (redLight) redLight.classList.add('active');
            break;
        case 'yellow':
            if (yellowLight) yellowLight.classList.add('active');
            break;
        case 'green':
            if (greenLight) greenLight.classList.add('active');
            break;
    }
}

function showError(message) {
    showStatus(message, 'danger');
}

function showStatus(message, type) {
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
    
    // Auto-eliminar después de 5 segundos (solo para success)
    if (type === 'success') {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Utilidades adicionales
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString();
}

// Exportar funciones para uso global
window.trafficApp = {
    updateMetrics,
    updateTrafficLights,
    showError,
    showStatus
};

// Forzar actualización manual (para debugging)
window.forceUpdate = function() {
    console.log('🔄 Forzando actualización manual...');
    updateMetrics();
    updateTrafficLights();
};