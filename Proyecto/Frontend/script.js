// Variables globales
let charts = {};
let realTimeData = {
    cpu: [],
    memory: [],
    battery: [],
    temperature: []
};
let maxDataPoints = 20;
let updateInterval;

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    connectToBackend();
    startDataUpdates();
});

const i18n = {
    es: {
        connected: 'Dispositivo conectado',
        disconnected: 'Dispositivo no conectado',
        battery: {
            discharging: 'Descargando',
            charged: 'Cargado',
            low: 'Baja',
            unknown: 'Desconocido'
        }
    }
    // Apartado para agregar mas idiomas
}

// Inicializar todos los gráficos
function initializeCharts() {
    // Configuración común para gráficos pequeños
    const miniChartConfig = {
        type: 'line',
        options: {
            responsive: false,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: { display: false }
            },
            elements: {
                point: { radius: 0 },
                line: { tension: 0.4, borderWidth: 2 }
            },
            animation: { duration: 0 }
        }
    };

    // Gráfico de CPU
    charts.cpuMini = new Chart(document.getElementById('cpuChart'), {
        ...miniChartConfig,
        data: {
            labels: Array(maxDataPoints).fill(''),
            datasets: [{
                data: Array(maxDataPoints).fill(0),
                borderColor: '#4a6cf7',
                backgroundColor: 'rgba(74, 108, 247, 0.1)',
                fill: true
            }]
        }
    });

    // Gráfico de Memoria
    charts.memoryMini = new Chart(document.getElementById('memoryChart'), {
        ...miniChartConfig,
        data: {
            labels: Array(maxDataPoints).fill(''),
            datasets: [{
                data: Array(maxDataPoints).fill(0),
                borderColor: '#ff9a9e',
                backgroundColor: 'rgba(255, 154, 158, 0.1)',
                fill: true
            }]
        }
    });

    // Gráfico de Temperatura
    charts.tempMini = new Chart(document.getElementById('tempChart'), {
        ...miniChartConfig,
        data: {
            labels: Array(maxDataPoints).fill(''),
            datasets: [{
                data: Array(maxDataPoints).fill(0),
                borderColor: '#ff6384',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                fill: true
            }]
        }
    });

    // Gráfico principal
    charts.main = new Chart(document.getElementById('mainChart'), {
        type: 'line',
        data: {
            labels: Array(maxDataPoints).fill(''),
            datasets: [
                {
                    label: 'CPU',
                    data: Array(maxDataPoints).fill(0),
                    borderColor: '#4a6cf7',
                    backgroundColor: 'rgba(74, 108, 247, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Memoria',
                    data: Array(maxDataPoints).fill(0),
                    borderColor: '#ff9a9e',
                    backgroundColor: 'rgba(255, 154, 158, 0.1)',
                    fill: true,
                    tension: 0.4,
                    hidden: true
                },
                {
                    label: 'Batería',
                    data: Array(maxDataPoints).fill(0),
                    borderColor: '#4facfe',
                    backgroundColor: 'rgba(79, 172, 254, 0.1)',
                    fill: true,
                    tension: 0.4,
                    hidden: true
                },
                {
                    label: 'Temperatura',
                    data: Array(maxDataPoints).fill(0),
                    borderColor: '#ff6384',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    fill: true,
                    tension: 0.4,
                    hidden: true
                }
            ]
        },
        options: {
            responsive: false,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#333',
                        usePointStyle: true
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#666' }
                },
                y: {
                    min: 0,
                    max: 100, // Valor inicial para CPU/Batería
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    ticks: { color: '#666' }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            },
            animation: {
                duration: 0
            }
        }
    });

    // Event listener para el selector de gráficos
    document.getElementById('chartSelector').addEventListener('change', function(e) {
        const selectedMetric = normalize(e.target.value);
        
        // Ocultar todos los datasets
        charts.main.data.datasets.forEach(dataset => {
            dataset.hidden = true;
        });
        
        // Mostrar solo el seleccionado
        const datasetIndex = charts.main.data.datasets.findIndex(d => normalize(d.label) === selectedMetric);
        if (datasetIndex !== -1) {
            charts.main.data.datasets[datasetIndex].hidden = false;
            
            // Ajustar escala Y si es necesario
            if (selectedMetric === 'temperature') {
                charts.main.options.scales.y.min = 0;
                charts.main.options.scales.y.max = 50; // Ajustar según necesidades
            } else if (selectedMetric === 'memory') {
                charts.main.options.scales.y.min = 0;
                charts.main.options.scales.y.max = 200;
            } else {
                charts.main.options.scales.y.min = 0;
                charts.main.options.scales.y.max = 100;
            }
        }
        charts.main.update();
    });
}

// Función para normalizar texto (minúsculas y sin acentos)
function normalize(str) {
    return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

// Simular conexión con el backend (reemplazar con conexión real)
function connectToBackend() {
    // En una implementación real, aquí se conectaría via WebSockets o API REST
    // Ejemplo:
    // fetch('/api/metrics').then(...)
    // o
    // const socket = new WebSocket('ws://...');
    // socket.onmessage = (event) => { ... }
    console.log("Conectando al backend...");
    
    // Simular conexión exitosa después de 2 segundos
    setTimeout(() => {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.connection-status');
        statusDot.classList.add('connected');
        statusText.textContent = i18n.es.connected;
        
        // Simular recepción de datos iniciales
        simulateInitialData();
    }, 2000);
}

// Simular datos iniciales
function simulateInitialData() {
    // Datos de ejemplo para inicializar las gráficas
    const now = new Date();
    for (let i = maxDataPoints - 1; i >= 0; i--) {
        const time = new Date(now - i * 1000).toLocaleTimeString();
        
        realTimeData.cpu.push({ time, value: Math.random() * 100 });
        realTimeData.memory.push({ time, value: 30 + Math.random() * 50 });
        realTimeData.battery.push({ time, value: 80 - i * 0.1 });
        realTimeData.temperature.push({ time, value: 25 + Math.random() * 10 });
    }
    
    updateAllCharts();
}

// Iniciar actualizaciones de datos
function startDataUpdates() {
    // En una implementación real, esto vendría del backend via WebSockets
    updateInterval = setInterval(() => {
        simulateDataUpdate();
    }, 1000);
}

// Simular actualización de datos
function simulateDataUpdate() {
    const now = new Date().toLocaleTimeString();
    
    // Generar nuevos valores (en una app real estos vendrían del backend)
    const newCpu = Math.random() * 100;
    const newMemory = 30 + Math.random() * 50;
    const newBattery = Math.max(0, realTimeData.battery[realTimeData.battery.length - 1].value - 0.1);
    const newTemperature = 25 + Math.random() * 10;
    
    // Añadir nuevos datos
    realTimeData.cpu.push({ time: now, value: newCpu });
    realTimeData.memory.push({ time: now, value: newMemory });
    realTimeData.battery.push({ time: now, value: newBattery });
    realTimeData.temperature.push({ time: now, value: newTemperature });
    
    // Mantener solo los últimos maxDataPoints puntos
    if (realTimeData.cpu.length > maxDataPoints) {
        realTimeData.cpu.shift();
        realTimeData.memory.shift();
        realTimeData.battery.shift();
        realTimeData.temperature.shift();
    }
    
    // Actualizar la interfaz
    updateMetricDisplays(newCpu, newMemory, newBattery, newTemperature);
    updateAllCharts();
    simulateProcessList();
}

// Actualizar las displays de métricas
function updateMetricDisplays(cpu, memory, battery, temperature) {
    // Validación de datos
    cpu = isFinite(cpu) ? cpu : 0;
    memory = isFinite(memory) ? memory : 0;
    battery = isFinite(battery) ? battery : 0;
    temperature = isFinite(temperature) ? temperature : 0;

    animateMetric('cpuValue')
    animateMetric('memoryValue')
    animateMetric('batteryValue')
    animateMetric('temperatureValue')

    document.getElementById('cpuValue').textContent = `${cpu.toFixed(1)}%`;
    document.getElementById('memoryValue').textContent = `${memory.toFixed(1)} MB`;
    document.getElementById('batteryValue').textContent = `${battery.toFixed(1)}%`;
    document.getElementById('temperatureValue').textContent = `${temperature.toFixed(1)}°C`;
    
    // Actualizar barras de progreso
    document.getElementById('cpuProgress').style.width = `${cpu}%`;
    document.getElementById('memoryProgress').style.width = `${memory/200*100}%`; // Suponiendo 200MB como máximo
    document.getElementById('batteryProgress').style.width = `${battery}%`;
    document.getElementById('temperatureProgress').style.width = `${temperature/50*100}%`;
    
    // Actualizar estado de batería
    const batteryStatus = document.getElementById('batteryStatus');
    if (battery > 70) {
        batteryStatus.textContent = i18n.es.battery.charged;
        batteryStatus.style.color = 'var(--success)';
    } else if (battery > 30) {
        batteryStatus.textContent = i18n.es.battery.discharging;
        batteryStatus.style.color = 'var(--warning)';
    } else {
        batteryStatus.textContent = i18n.es.battery.low;
        batteryStatus.style.color = 'var(--danger)';
    }
}

function animateMetric(id){
    const el = document.getElementById(id);
    el.classList.add('updated');
    setTimeout(() => el.classList.remove('updated'), 300)
}

// Actualizar todos los gráficos
function updateAllCharts() {
    window.requestAnimationFrame(() => {
        // Actualizar gráficos mini
        updateMiniChart(charts.cpuMini, realTimeData.cpu.map(d => d.value));
        updateMiniChart(charts.memoryMini, realTimeData.memory.map(d => d.value));
        updateMiniChart(charts.tempMini, realTimeData.temperature.map(d => d.value));
        
        // Actualizar gráfico principal
        const labels = realTimeData.cpu.map(d => d.time);
        charts.main.data.labels = labels;
        charts.main.data.datasets[0].data = realTimeData.cpu.map(d => d.value);
        charts.main.data.datasets[1].data = realTimeData.memory.map(d => d.value);
        charts.main.data.datasets[2].data = realTimeData.battery.map(d => d.value);
        charts.main.data.datasets[3].data = realTimeData.temperature.map(d => d.value);
        charts.main.update();
    })
}

// Actualizar gráficos mini
function updateMiniChart(chart, data) {
    chart.data.datasets[0].data = data;
    chart.update();
}

// Simular lista de procesos (reemplazar con datos reales del backend)
function simulateProcessList() {
    const processes = [
        { name: 'com.android.systemui', cpu: (Math.random() * 15).toFixed(1), memory: (50 + Math.random() * 100).toFixed(1) },
        { name: 'com.google.android.gms', cpu: (Math.random() * 10).toFixed(1), memory: (80 + Math.random() * 120).toFixed(1) },
        { name: 'com.spotify.music', cpu: (Math.random() * 20).toFixed(1), memory: (100 + Math.random() * 150).toFixed(1) },
        { name: 'com.facebook.katana', cpu: (Math.random() * 25).toFixed(1), memory: (120 + Math.random() * 180).toFixed(1) },
        { name: 'com.whatsapp', cpu: (Math.random() * 8).toFixed(1), memory: (70 + Math.random() * 90).toFixed(1) }
    ];
    
    // Ordenar por uso de CPU
    processes.sort((a, b) => parseFloat(b.cpu) - parseFloat(a.cpu));
    
    // Actualizar la lista en el DOM
    const processList = document.getElementById('processList');
    processList.innerHTML = '';
    
    processes.forEach(proc => {
        const item = document.createElement('div');
        item.className = 'process-item';
        item.innerHTML = `
            <span>${proc.name}</span>
            <span>${proc.cpu}%</span>
            <span>${proc.memory} MB</span>
        `;
        processList.appendChild(item);
    });
}

// Limpiar intervalo cuando la página se cierre
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});