function updateMetrics() {
    fetch('/metrics')
        .then(response => response.json())
        .then(data => {
            const statusElement = document.getElementById('analysisStatus');
            const countsContainer = document.getElementById('objectCountsContainer');
            const totalObjectsElement = document.getElementById('totalObjects');

            statusElement.textContent = data.status;
            statusElement.className = 'status-badge ' +
                (data.status === 'Detectando' ? 'status-detecting' : 'status-no-detection');

            let countsHtml = '<h3>Conteo por Clase (Vehículos):</h3>';
            let total = 0;

            if (Object.keys(data.counts).length > 0) {

                const initialLoadMsg = document.getElementById('initial-load-msg');
                if (initialLoadMsg) {
                    initialLoadMsg.style.display = 'none';
                }

                for (const [cls, num] of Object.entries(data.counts)) {
                    const count = parseInt(num, 10);

                    countsHtml += `
                                <div class="metric-card object-count-card">
                                    ${cls}:
                                    <strong>${count}</strong>
                                </div>
                            `;
                    total += count;
                }

                countsContainer.innerHTML = countsHtml;


            } else {
                const initialLoadMsg = document.getElementById('initial-load-msg');
                if (initialLoadMsg) {
                    initialLoadMsg.style.display = 'block';
                    initialLoadMsg.textContent = data.status === 'Sin detecciones' ? 'Sin detecciones en el momento.' : 'Esperando detecciones...';
                }

                countsContainer.innerHTML = `
                            <h3>Conteo por Clase (Vehículos):</h3>
                            <p id="initial-load-msg">${data.status === 'Sin detecciones' ? 'Sin detecciones en el momento.' : 'Esperando detecciones...'}</p>
                        `;
            }

            totalObjectsElement.textContent = total;

        })
        .catch(error => console.error('Error al obtener métricas:', error));
}

setInterval(updateMetrics, 500); 