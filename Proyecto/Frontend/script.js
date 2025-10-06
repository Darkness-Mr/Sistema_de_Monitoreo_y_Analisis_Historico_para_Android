// URL del backend (si sirves frontend en 8080)
const API = 'http://127.0.0.1:5000';

// Variables globales
let charts = {};
let realTimeData = { cpu: [], memory: [], battery: [], temperature: [] };
let maxDataPoints = 20;
let updateInterval;

// Inicialización cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function () {
  initializeCharts();
  initializeMainChart();   // <- se llama aquí, después de crear charts
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
  // Apartado para agregar más idiomas
};

// -------------------------------------
// Gráficos
// -------------------------------------
function initializeCharts() {
  // Config común para mini charts
  const miniChartConfig = {
    type: 'line',
    options: {
      responsive: false,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false } },
      elements: { point: { radius: 0 }, line: { tension: 0.4, borderWidth: 2 } },
      animation: { duration: 0 }
    }
  };

  // Mini CPU
  charts.cpuMini = new Chart(document.getElementById('cpuChart'), {
    ...miniChartConfig,
    data: {
      labels: Array(maxDataPoints).fill(''),
      datasets: [{
        data: Array(maxDataPoints).fill(0),
        borderColor: '#4a6cf7',
        backgroundColor: 'rgba(74,108,247,0.1)',
        fill: true
      }]
    }
  });

  // Mini Memoria
  charts.memoryMini = new Chart(document.getElementById('memoryChart'), {
    ...miniChartConfig,
    data: {
      labels: Array(maxDataPoints).fill(''),
      datasets: [{
        data: Array(maxDataPoints).fill(0),
        borderColor: '#ff9a9e',
        backgroundColor: 'rgba(255,154,158,0.1)',
        fill: true
      }]
    }
  });

  // Mini Temperatura
  charts.tempMini = new Chart(document.getElementById('tempChart'), {
    ...miniChartConfig,
    data: {
      labels: Array(maxDataPoints).fill(''),
      datasets: [{
        data: Array(maxDataPoints).fill(0),
        borderColor: '#ff6384',
        backgroundColor: 'rgba(255,99,132,0.1)',
        fill: true
      }]
    }
  });

  // Gráfico principal
  charts.main = new Chart(document.getElementById('mainChart'), {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        { label: 'CPU',         data: [], borderColor: '#4a6cf7', backgroundColor: 'rgba(74,108,247,0.1)', fill: true, tension: 0.4, hidden: false },
        { label: 'Memoria',     data: [], borderColor: '#ff9a9e', backgroundColor: 'rgba(255,154,158,0.1)', fill: true, tension: 0.4, hidden: true },
        { label: 'Batería',     data: [], borderColor: '#4facfe', backgroundColor: 'rgba(79,172,254,0.1)',   fill: true, tension: 0.4, hidden: true },
        { label: 'Temperatura', data: [], borderColor: '#ff6384', backgroundColor: 'rgba(255,99,132,0.1)',  fill: true, tension: 0.4, hidden: true }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#666' } },
        y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: '#666' } }
      },
      interaction: { mode: 'index', intersect: false },
      animation: { duration: 0 }
    }
  });

  // Selector de datasets
  document.getElementById('chartSelector').addEventListener('change', function(e) {
    const selected = e.target.value;
    charts.main.data.datasets.forEach(d => d.hidden = true);
    let idx = 0;
    if (selected === 'cpu') idx = 0;
    if (selected === 'memory') idx = 1;
    if (selected === 'battery') idx = 2;
    if (selected === 'temperature') idx = 3;

    // Ajusta eje Y
    charts.main.options.scales.y.min = 0;
    charts.main.options.scales.y.max = (selected === 'temperature') ? 100 : 100; // puedes cambiar rango para °C si quieres
    charts.main.data.datasets[idx].hidden = false;
    charts.main.update('none');
  });
}

function initializeMainChart() {
  charts.main.data.datasets.forEach(d => d.hidden = true);
  charts.main.data.datasets[0].hidden = false; // CPU visible
  charts.main.options.scales.y.min = 0;
  charts.main.options.scales.y.max = 100;
  charts.main.update('none');
}

function updateAllCharts() {
  const labels = realTimeData.cpu.map(d => d.time);

  charts.main.data.labels = labels;
  charts.main.data.datasets[0].data = realTimeData.cpu.map(d => +d.value || 0);
  charts.main.data.datasets[1].data = realTimeData.memory.map(d => +d.value || 0);      // % RAM usada
  charts.main.data.datasets[2].data = realTimeData.battery.map(d => +d.value || 0);     // %
  charts.main.data.datasets[3].data = realTimeData.temperature.map(d => +d.value || 0); // °C
  charts.main.update('none');

  updateMiniChart(charts.cpuMini,    realTimeData.cpu.map(d => +d.value || 0));
  updateMiniChart(charts.memoryMini, realTimeData.memory.map(d => +d.value || 0));
  updateMiniChart(charts.tempMini,   realTimeData.temperature.map(d => +d.value || 0));
}

function updateMiniChart(chart, data) {
  chart.data.labels = Array(data.length).fill('');
  chart.data.datasets[0].data = data;
  chart.update('none');
}

// -------------------------------------
// Backend & polling
// -------------------------------------
async function connectToBackend() {
  try {
    const st = await fetch(`${API}/api/status`).then(r => r.json());
    const dot = document.querySelector('.status-dot');
    const statusBox = document.getElementById('connectionStatus');
    if (st.device_connected) {
      dot.classList.add('connected');
      statusBox.childNodes.forEach(n => { if (n.nodeType === Node.TEXT_NODE) n.textContent = ' Dispositivo conectado'; });
    } else {
      dot.classList.remove('connected');
      statusBox.childNodes.forEach(n => { if (n.nodeType === Node.TEXT_NODE) n.textContent = ' Dispositivo no conectado'; });
    }
  } catch {
    const dot = document.querySelector('.status-dot');
    const statusBox = document.getElementById('connectionStatus');
    dot.classList.remove('connected');
    statusBox.childNodes.forEach(n => { if (n.nodeType === Node.TEXT_NODE) n.textContent = ' Dispositivo no conectado'; });
  }
}

function startDataUpdates() {
  if (updateInterval) clearInterval(updateInterval);
  updateInterval = setInterval(fetchAndUpdate, 1000);
}

async function fetchAndUpdate() {
  try {
    const m = await fetch(`${API}/api/metrics`).then(r => r.json());

    // CPU 0–100
    const cpuRaw = Number(m.cpu_usage);
    const cpu = Number.isFinite(cpuRaw) ? Math.max(0, Math.min(100, cpuRaw)) : 0;

    // Memoria
    const { usedMB, usedPct } = parseMemory(m.memory_info);

    // Batería y temperatura
    const battery = parseInt(m.battery_info?.level ?? 0) || 0;
    const tempDeci = parseInt(m.battery_info?.temperature ?? 0) || 0;
    const temperature = tempDeci / 10;

    // Tarjetas
    updateMetricDisplays(cpu, usedMB, battery, temperature, usedPct);

    // Series del gráfico
    const now = new Date().toLocaleTimeString();
    pushPoint('cpu',         { time: now, value: cpu });
    pushPoint('memory',      { time: now, value: usedPct });
    pushPoint('battery',     { time: now, value: battery });
    pushPoint('temperature', { time: now, value: temperature });

    updateAllCharts();

    if (Array.isArray(m.processes)) updateProcessList(m.processes);
  } catch (e) {
    console.error(e);
  }
}

// -------------------------------------
// Helpers UI
// -------------------------------------
function updateMetricDisplays(cpu, memoryUsedMB, battery, temperature, memPct = null) {
  // Validación
  cpu = isFinite(cpu) ? cpu : 0;
  memoryUsedMB = isFinite(memoryUsedMB) ? memoryUsedMB : 0;
  battery = isFinite(battery) ? battery : 0;
  temperature = isFinite(temperature) ? temperature : 0;

  animateMetric('cpuValue');
  animateMetric('memoryValue');
  animateMetric('batteryValue');
  animateMetric('temperatureValue');

  document.getElementById('cpuValue').textContent = `${cpu.toFixed(1)}%`;
  document.getElementById('memoryValue').textContent = `${memoryUsedMB.toFixed(1)} MB`;
  document.getElementById('batteryValue').textContent = `${battery.toFixed(1)}%`;
  document.getElementById('temperatureValue').textContent = `${temperature.toFixed(1)}°C`;

  // Barras
  document.getElementById('cpuProgress').style.width = `${Math.min(100, cpu)}%`;
  document.getElementById('batteryProgress').style.width = `${Math.min(100, battery)}%`;
  document.getElementById('temperatureProgress').style.width = `${Math.min(100, (temperature / 50) * 100)}%`;
  if (memPct !== null) {
    document.getElementById('memoryProgress').style.width = `${Math.min(100, memPct)}%`;
  }

  // Estado batería
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

function animateMetric(id) {
  const el = document.getElementById(id);
  el.classList.add('updated');
  setTimeout(() => el.classList.remove('updated'), 300);
}

// Memoria desde /proc/meminfo
function parseMemory(meminfo = {}) {
  const toKB = v => {
    if (!v) return 0;
    const num = String(v).trim().split(/\s+/)[0];
    return parseInt(num) || 0;
  };
  const totalKB = toKB(meminfo.MemTotal);
  const availKB = toKB(meminfo.MemAvailable);
  const usedKB = Math.max(0, totalKB - availKB);
  const usedMB = usedKB / 1024;
  const usedPct = totalKB ? (usedKB / totalKB) * 100 : 0;
  return { totalKB, availKB, usedKB, usedMB, usedPct };
}

function pushPoint(key, point) {
  realTimeData[key].push(point);
  if (realTimeData[key].length > maxDataPoints) realTimeData[key].shift();
}

function updateProcessList(processes) {
  const processList = document.getElementById('processList');
  processList.innerHTML = '';

  if (!Array.isArray(processes) || processes.length === 0) {
    const item = document.createElement('div');
    item.className = 'process-item';
    item.innerHTML = `<span>Sin datos de procesos</span><span>-</span><span>-</span>`;
    processList.appendChild(item);
    return;
  }

  // Ordena por CPU desc (por si viene desordenado)
  const rows = [...processes].sort((a, b) => (b.cpu || 0) - (a.cpu || 0));

  rows.forEach(p => {
    const item = document.createElement('div');
    item.className = 'process-item';
    item.innerHTML = `
      <span title="PID ${p.pid || ''}">${p.name || ''}</span>
      <span>${Number(p.cpu || 0).toFixed(1)}%</span>
      <span>${Number(p.memory || 0).toFixed(1)} MB</span>
    `;
    processList.appendChild(item);
  });
}

// Limpieza
window.addEventListener('beforeunload', () => {
  if (updateInterval) clearInterval(updateInterval);
});
