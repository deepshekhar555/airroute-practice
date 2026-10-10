const form = document.querySelector('#prediction-form');
const audienceSelect = document.querySelector('#audience');
const sliders = {
  day_num: document.querySelector('#day-num'),
  pm25: document.querySelector('#pm25'),
  pm10: document.querySelector('#pm10'),
};

const labels = {
  day_num: ['#day-output', ''],
  pm25: ['#pm25-output', ' μg/m³'],
  pm10: ['#pm10-output', ' μg/m³'],
};

function updateSlider(input, key) {
  const [output, suffix] = labels[key];
  document.querySelector(output).textContent = `${input.value}${suffix}`;
}

Object.entries(sliders).forEach(([key, input]) => {
  input.addEventListener('input', () => updateSlider(input, key));
});

function categoryFor(aqi) {
  if (aqi <= 50) return ['Good', 'low'];
  if (aqi <= 100) return ['Satisfactory', 'low'];
  if (aqi <= 200) return ['Moderate', 'moderate'];
  if (aqi <= 300) return ['Poor', 'high'];
  if (aqi <= 400) return ['Very Poor', 'high'];
  return ['Severe', 'critical'];
}

function audienceGuidance(aqi, audience) {
  const generic = {
    general: 'Reduce outdoor exertion and keep indoor air cleaner during this period.',
    children: 'Keep children indoors for longer periods and avoid school play or cycling in heavy pollution.',
    elderly: 'Limit outdoor exposure and avoid prolonged walks or commuting in poor air quality.',
    outdoor: 'Plan outdoor work around safer windows and take breaks indoors whenever possible.',
    asthma: 'Avoid strenuous activity and keep medication nearby; consider a mask on high-AQI hours.',
  };

  if (aqi <= 50) {
    return { recommendation: 'Air quality is comfortable. Continue regular outdoor activities.', safeWindow: 'Good for outdoor time', actions: ['Continue normal activities.', 'Keep routine checks for local updates.'] };
  }
  if (aqi <= 100) {
    return { recommendation: generic[audience] || generic.general, safeWindow: 'Best before midday', actions: ['Limit long outdoor sessions.', 'Choose indoor activity during peak pollution hours.'] };
  }
  if (aqi <= 150) {
    return { recommendation: generic[audience] || generic.general, safeWindow: 'Avoid midday outdoors', actions: ['Use a mask when outside.', 'Reduce exercise intensity outdoors.'] };
  }
  if (aqi <= 200) {
    return { recommendation: generic[audience] || generic.general, safeWindow: 'Stay indoors', actions: ['Keep windows closed.', 'Move workouts and commutes indoors if possible.'] };
  }
  return { recommendation: generic[audience] || generic.general, safeWindow: 'Avoid outdoor exposure', actions: ['Avoid non-essential outdoor time.', 'Use filtered air indoors and follow local guidance.'] };
}

async function predict() {
  const payload = Object.fromEntries(Object.entries(sliders).map(([key, input]) => [key, Number(input.value)]));
  payload.audience = audienceSelect.value;
  try {
    const response = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error('Prediction request failed');
    const data = await response.json();
    renderResult(data);
  } catch (error) {
    document.querySelector('#api-status').textContent = 'API unavailable — run airroute locally';
    document.querySelector('#result-aqi').textContent = '—';
  }
}

function renderResult(data) {
  const aqi = data.predicted_aqi;
  const [category, risk] = categoryFor(aqi);
  const audience = audienceSelect.value;
  const profile = audienceGuidance(aqi, audience);
  const riskLevel = data.risk_level || (risk === 'critical' ? 'Critical exposure' : risk === 'high' ? 'High exposure' : risk === 'moderate' ? 'Elevated exposure' : 'Low exposure');
  const recommendation = data.recommendation || profile.recommendation;
  const safeWindow = data.safe_window || profile.safeWindow;
  const actions = data.safety_actions && data.safety_actions.length ? data.safety_actions : profile.actions;

  document.querySelector('#result-aqi').textContent = aqi;
  document.querySelector('#hero-aqi').textContent = aqi;
  document.querySelector('#result-category').textContent = data.category || category;
  document.querySelector('#hero-category').textContent = data.category || category;
  document.querySelector('#hero-pm25').textContent = sliders.pm25.value;
  document.querySelector('#hero-pm10').textContent = sliders.pm10.value;
  document.querySelector('#risk-level').textContent = riskLevel;
  document.querySelector('#safe-window').textContent = safeWindow;
  document.querySelector('#recommendation').textContent = recommendation;
  document.querySelector('#api-status').textContent = 'Connected to local AirRoute API';

  const list = document.querySelector('#safety-actions');
  list.innerHTML = actions.map((item) => `<li>${item}</li>`).join('');
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  predict();
});

audienceSelect.addEventListener('change', () => {
  const snapshot = document.querySelector('#result-aqi').textContent;
  if (snapshot && snapshot !== '—') {
    const current = Number(snapshot);
    renderResult({ predicted_aqi: current, category: document.querySelector('#result-category').textContent, risk_level: document.querySelector('#risk-level').textContent, recommendation: document.querySelector('#recommendation').textContent, safety_actions: Array.from(document.querySelectorAll('#safety-actions li')).map((item) => item.textContent) });
  }
});

Object.values(sliders).forEach((input) => {
  updateSlider(input, Object.keys(sliders).find((key) => sliders[key] === input));
});

function loadTasks() {
  const storedTasks = JSON.parse(localStorage.getItem('airroute-plan') || '[]');
  const list = document.querySelector('#task-list');
  const count = document.querySelector('#task-count');
  count.textContent = `${storedTasks.length} ${storedTasks.length === 1 ? 'task' : 'tasks'}`;
  if (!storedTasks.length) {
    list.innerHTML = '<div class="empty-state"><span>⌁</span><strong>No tasks yet</strong><p>Add your first project goal to begin.</p></div>';
    return;
  }
  list.innerHTML = storedTasks.map((task) => `
    <div class="task-item"><span class="task-check">✓</span><div><strong>${task.title}</strong><small>${task.track} · ${task.created_at}</small></div></div>
  `).join('');
}

document.querySelector('#task-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const title = document.querySelector('#task-title').value.trim();
  const track = document.querySelector('#task-track').value;
  try {
    const response = await fetch('/api/planner', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, track }),
    });
    if (!response.ok) throw new Error('Planner request failed');
    const data = await response.json();
    const tasks = JSON.parse(localStorage.getItem('airroute-plan') || '[]');
    tasks.push({ ...data.task, created_at: 'Just now' });
    localStorage.setItem('airroute-plan', JSON.stringify(tasks));
    document.querySelector('#task-title').value = '';
    loadTasks();
  } catch (error) {
    document.querySelector('#task-list').innerHTML = '<div class="api-error">Start the local API to save project tasks.</div>';
  }
});

loadTasks();

predict();
