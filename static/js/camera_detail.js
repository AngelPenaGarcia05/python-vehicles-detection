// Configuración
const UPDATE_INTERVAL = 2000;
let currentCameraId = typeof CURRENT_CAMERA_ID !== 'undefined' ? CURRENT_CAMERA_ID : 0;
let aiEnabled = typeof AI_ENABLED !== 'undefined' ? AI_ENABLED : true;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log(`📷 Inicializando vista de cámara ${currentCameraId}...`);
    console.log('🔍 Estado IA:', aiEnabled);
    initializeCameraView();
});

function initializeCameraView() {
    setInterval(updateCameraMetrics, UPDATE_INTERVAL);
    updateCameraMetrics(); // Primera actualización inmediata
}

function updateCameraMetrics() {
    fetch(`/camera_metrics/${currentCameraId}`)
        .then(response => {
            if (!response.ok) throw new Error('Error en respuesta');
            return response.json();
        })
        .then(data => {
            console.log('📊 Datos de cámara:', data);
            updateCameraDisplay(data);
            updateVehicleDistribution(data.classes);
            updateDetectionsTable(data.detections);
        })
        .catch(error => {
            console.error('❌ Error actualizando métricas de cámara:', error);
        });
}

function updateCameraDisplay(data) {
    // Total de vehículos
    const totalElement = document.getElementById('cameraTotalVehicles');
    if (totalElement) {
        totalElement.textContent = data.count;
    }

    // Congestión
    const congestionElement = document.getElementById('cameraCongestion');
    const congestionBox = document.getElementById('congestionBox');
    
    if (congestionElement && congestionBox) {
        congestionElement.textContent = data.congestion;
        congestionBox.className = `metric-box bg-${data.congestion_badge} text-${data.congestion_badge === 'warning' ? 'dark' : 'white'} p-3 rounded`;
    }
}

function updateVehicleDistribution(classes) {
    const container = document.getElementById('vehicleDistribution');
    if (!container) return;
    
    if (Object.keys(classes).length === 0) {
        container.innerHTML = '<div class="text-muted">No hay vehículos detectados</div>';
        return;
    }
    
    let html = '';
    const totalVehicles = Object.values(classes).reduce((a, b) => a + b, 0);
    
    for (const [vehicleType, count] of Object.entries(classes)) {
        const percentage = totalVehicles > 0 ? (count / totalVehicles) * 100 : 0;
        
        html += `
            <div class="mb-2">
                <div class="d-flex justify-content-between small">
                    <span>${vehicleType}:</span>
                    <span class="fw-bold">${count} (${percentage.toFixed(1)}%)</span>
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar" style="width: ${percentage}%"></div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function updateDetectionsTable(detections) {
    const tableBody = document.getElementById('detectionsTable');
    if (!tableBody) return;
    
    if (detections.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No hay detecciones activas</td></tr>';
        return;
    }
    
    let html = '';
    detections.forEach((detection, index) => {
        html += `
            <tr>
                <td>
                    <i class="fas fa-car me-2"></i>
                    ${detection.class}
                </td>
                <td>
                    <span class="badge bg-info">${(detection.confidence * 100).toFixed(1)}%</span>
                </td>
                <td>
                    <small>(${detection.bbox[0]}, ${detection.bbox[1]})</small>
                </td>
                <td>
                    <div class="color-indicator" style="background-color: rgb(${detection.color[0]}, ${detection.color[1]}, ${detection.color[2]})"></div>
                </td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Forzar actualización manual
window.forceUpdate = function() {
    updateCameraMetrics();
};