const state = { token: localStorage.getItem('token'), user: JSON.parse(localStorage.getItem('user') || 'null'), activeView: 'dashboard' };
const PAGE_SIZE = 5;
const tableStates = {};
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const viewMeta = {
  dashboard: { icon: '▦', title: 'Dashboard', text: 'Resumen operativo del sistema comunitario de agua.' },
  agua: { icon: '≋', title: 'Agua almacenada', text: 'Control visual de cisterna, lecturas y umbrales de abastecimiento.' },
  viviendas: { icon: '⌂', title: 'Viviendas y censo', text: 'Registro de casas, propietarios y habitantes de la comunidad.' },
  consumos: { icon: '◷', title: 'Consumo mensual', text: 'Seguimiento por período para detectar patrones y consumos anómalos.' },
  pagos: { icon: 'Q', title: 'Pagos', text: 'Control de cuotas, recibos y morosidad por vivienda.' },
  distribucion: { icon: '◇', title: 'Distribución', text: 'Planificación semanal de horarios para el servicio de agua.' },
  mantenimiento: { icon: '⚙', title: 'Mantenimiento', text: 'Órdenes, responsables e intervenciones técnicas.' },
  notificaciones: { icon: '!', title: 'Notificaciones', text: 'Alertas relevantes para el rol activo.' },
  usuarios: { icon: '+', title: 'Usuarios', text: 'Creación de cuentas y asignación de roles desde administración.' },
};

function viewHero(viewId) {
  const meta = viewMeta[viewId];
  if (!meta) return '';
  return `
    <div class="view-hero">
      <div class="view-hero-copy">
        <span class="screen-icon">${meta.icon}</span>
        <div>
          <h1>${meta.title}</h1>
          <p>${meta.text}</p>
        </div>
      </div>
      <img src="/static/img/dashboard-water.png" alt="" />
    </div>`;
}

function decorateViewHeaders() {
  Object.keys(viewMeta).forEach((viewId) => {
    const section = $(`#${viewId}`);
    if (!section || section.querySelector('.view-hero')) return;
    section.insertAdjacentHTML('afterbegin', viewHero(viewId));
  });
}

function toast(message, isError = false) {
  const box = $('#toast');
  box.textContent = message;
  box.style.background = isError ? '#7f1d1d' : '#102027';
  box.classList.remove('hidden');
  setTimeout(() => box.classList.add('hidden'), 3200);
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const res = await fetch(`/api${path}`, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Error de comunicación con el servidor');
  return data;
}

function formData(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  form.querySelectorAll('input[type="checkbox"]').forEach(ch => data[ch.name] = ch.checked);
  Object.keys(data).forEach(k => data[k] === '' && delete data[k]);
  return data;
}

function table(rows, columns) {
  if (!rows?.length) return '<p class="muted">No hay datos para mostrar.</p>';
  return `<div class="table-wrap"><table><thead><tr>${columns.map(c => `<th>${c.label}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${columns.map(c => `<td>${c.render ? c.render(row) : (row[c.key] ?? '')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function paginationControls(tableId, totalItems, currentPage) {
  const totalPages = Math.ceil(totalItems / PAGE_SIZE);
  if (totalPages <= 1) return '';

  const buttons = [];
  buttons.push(`<button class="page-btn" type="button" data-table="${tableId}" data-action="prev" ${currentPage === 1 ? 'disabled' : ''}>Anterior</button>`);

  for (let i = 1; i <= totalPages; i += 1) {
    buttons.push(`<button class="page-btn ${i === currentPage ? 'active' : ''}" type="button" data-table="${tableId}" data-action="page" data-page="${i}">${i}</button>`);
  }

  buttons.push(`<button class="page-btn" type="button" data-table="${tableId}" data-action="next" ${currentPage === totalPages ? 'disabled' : ''}>Siguiente</button>`);

  return `<div class="table-pagination" data-table-pagination="${tableId}">${buttons.join('')}</div>`;
}

function renderTable(containerSelector, rows, columns, options = {}) {
  const container = $(containerSelector);
  if (!container) return;
  const tableId = options.id || containerSelector;
  const totalPages = Math.max(1, Math.ceil((rows?.length || 0) / PAGE_SIZE));
  const state = tableStates[tableId] || { page: 1 };
  state.page = Math.min(Math.max(state.page, 1), totalPages);
  tableStates[tableId] = { ...state, rows, columns, containerSelector, options };

  const start = (state.page - 1) * PAGE_SIZE;
  const pageRows = (rows || []).slice(start, start + PAGE_SIZE);
  container.innerHTML = `${table(pageRows, columns)}${paginationControls(tableId, rows.length, state.page)}`;
}

function renderConsumptionCalendar(rows, houseId) {
  const container = $('#consumptionCalendar');
  if (!container) return;

  if (!houseId) {
    container.innerHTML = '<p class="muted">Seleccione una vivienda para ver el calendario de consumos.</p>';
    return;
  }

  const registeredPeriods = new Set((rows || []).map(r => r.period));
  if (!registeredPeriods.size) {
    container.innerHTML = '<p class="muted">No hay consumos registrados para esta vivienda.</p>';
    return;
  }

  const today = new Date();
  const months = [];
  for (let i = 11; i >= 0; i -= 1) {
    const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    months.push({
      key,
      label: date.toLocaleString('es-ES', { month: 'short', year: 'numeric' }),
      active: registeredPeriods.has(key),
    });
  }

  container.innerHTML = months.map((month) => `
    <div class="calendar-cell ${month.active ? 'registered' : ''}">
      <strong>${month.label}</strong>
      <span>${month.active ? 'Registrado' : 'Sin registro'}</span>
    </div>
  `).join('');
}

function refreshTable(tableId) {
  const state = tableStates[tableId];
  if (!state) return;
  renderTable(state.containerSelector, state.rows, state.columns, state.options);
}

function applyRoleAccess() {
  const role = state.user?.role;
  if (!role) return;

  const visibleViewsByRole = {
    cliente: ['distribucion', 'mantenimiento', 'notificaciones'],
    empleado: ['dashboard', 'viviendas', 'pagos', 'notificaciones'],
    soporte: ['dashboard', 'mantenimiento', 'notificaciones'],
    administrador: ['dashboard', 'agua', 'viviendas', 'consumos', 'pagos', 'distribucion', 'mantenimiento', 'notificaciones', 'usuarios'],
  };
  const hiddenFormsByRole = {
    cliente: '#distributionForm, #maintenanceForm, #interventionForm, #cisternForm, #sensorForm, #houseForm, #residentForm, #consumptionForm, #paymentForm',
    empleado: '#distributionForm, #maintenanceForm, #interventionForm, #cisternForm, #sensorForm, #consumptionForm',
    soporte: '#distributionForm, #cisternForm, #sensorForm, #houseForm, #residentForm, #consumptionForm, #paymentForm',
    administrador: '',
  };

  const visibleViews = visibleViewsByRole[role] || [];
  $$('.nav-btn').forEach(btn => btn.classList.toggle('hidden', !visibleViews.includes(btn.dataset.view)));

  const allForms = '#distributionForm, #maintenanceForm, #interventionForm, #cisternForm, #sensorForm, #houseForm, #residentForm, #consumptionForm, #paymentForm';
  $$(allForms).forEach(form => form?.classList?.remove('hidden'));
  const hideSelector = hiddenFormsByRole[role];
  if (hideSelector) {
    $$(hideSelector).forEach(form => form?.classList?.add('hidden'));
  }

  const firstVisibleBtn = $$('.nav-btn').find(btn => !btn.classList.contains('hidden'));
  if (firstVisibleBtn) {
    $$('.nav-btn').forEach(b => b.classList.remove('active'));
    firstVisibleBtn.classList.add('active');
    $$('.view-section').forEach(s => s.classList.add('hidden'));
    const targetSection = $(`#${firstVisibleBtn.dataset.view}`);
    if (targetSection) targetSection.classList.remove('hidden');
    const pageTitle = $('#pageTitle');
    if (pageTitle) pageTitle.textContent = firstVisibleBtn.textContent;
    state.activeView = firstVisibleBtn.dataset.view;
  }
}

document.addEventListener('click', (event) => {
  const button = event.target.closest('.page-btn');
  if (!button) return;
  const tableId = button.dataset.table;
  const action = button.dataset.action;
  if (!tableId || !action) return;
  const state = tableStates[tableId];
  if (!state) return;

  const totalPages = Math.ceil((state.rows?.length || 0) / PAGE_SIZE);
  if (action === 'prev') {
    state.page = Math.max(1, state.page - 1);
  } else if (action === 'next') {
    state.page = Math.min(totalPages, state.page + 1);
  } else if (action === 'page') {
    state.page = Number(button.dataset.page) || state.page;
  }

  renderTable(state.containerSelector, state.rows, state.columns, state.options);
});

function setAuthVisible() {
  const logged = Boolean(state.token);
  $('#authView').classList.toggle('hidden', logged);
  $('#mainView').classList.toggle('hidden', !logged);
  if (logged) {
    $('#userLabel').textContent = `${state.user.firstName} ${state.user.lastName} · ${state.user.role}`;
    applyRoleAccess();
    loadAll();
  }
}

async function loadDashboard() {
  const data = await api('/dashboard');
  const c = data.cistern || { percentage: 0, currentLiters: 0, capacityLiters: 0 };
  $('#dashboard').innerHTML = `
    ${viewHero('dashboard')}
    <div class="cards">
      <div class="metric"><span><b class="metric-icon">≋</b>Nivel actual</span><strong>${Number(c.currentLiters || 0).toLocaleString()} L</strong><div class="water-bar"><div class="water-fill" style="width:${Math.min(c.percentage || 0, 100)}%"></div></div><small>${c.percentage || 0}% de capacidad</small></div>
      <div class="metric"><span><b class="metric-icon">⌂</b>Viviendas</span><strong>${data.houses}</strong><small>${data.residents} habitantes censados</small></div>
      <div class="metric"><span><b class="metric-icon">◷</b>Consumo registrado</span><strong>${Number(data.monthlyConsumptionLiters).toLocaleString()} L</strong><small>Histórico mensual</small></div>
      <div class="metric"><span><b class="metric-icon">↘</b>Días estimados</span><strong>${data.estimatedDaysRemaining ?? 'N/D'}</strong><small>Según consumo promedio</small></div>
      <div class="metric"><span><b class="metric-icon">Q</b>Pagos</span><strong>Q ${Number(data.paymentsTotal).toFixed(2)}</strong><small>Total registrado</small></div>
      <div class="metric"><span><b class="metric-icon">⚙</b>Mantenimientos</span><strong>${data.pendingMaintenance}</strong><small>Órdenes pendientes</small></div>
      <div class="metric"><span><b class="metric-icon">!</b>Notificaciones</span><strong>${data.unreadNotifications}</strong><small>No leídas</small></div>
      <div class="metric"><span><b class="metric-icon">↓</b>Consumo diario</span><strong>${Number(data.dailyConsumptionLiters || 0).toLocaleString()} L</strong><small>Con lecturas sucesivas</small></div>
    </div>
    <div class="grid two">
      <div class="card"><h2>Alertas recientes</h2>${renderNotifications(data.notifications)}</div>
      <div class="card"><h2>Distribución programada</h2><div id="dashboardDistributionTable"></div></div>
    </div>`;
  renderTable('#dashboardDistributionTable', data.distributionPlans, [
    {label:'Fecha', key:'serviceDate'}, {label:'Inicio', key:'startTime'}, {label:'Fin', key:'endTime'}, {label:'Notas', key:'notes'}
  ]);
}

function renderNotifications(items, options = {}) {
  const notifications = options.hideRead ? (items || []).filter(n => !n.isRead) : (items || []);
  if (!notifications.length) return '<p>No hay notificaciones.</p>';
  return notifications.map(n => {
    const isRead = Boolean(n.isRead);
    return `<article class="notification">
      <strong>${n.title}</strong>
      <span>${n.message}</span>
      <small>${n.notificationType} · ${new Date(n.createdAt).toLocaleString()}</small>
      ${!isRead && options.showMarkRead !== false ? `<button class="mark-read-btn" type="button" data-id="${n.id}">Visto</button>` : ''}
    </article>`;
  }).join('');
}

async function loadCistern() {
  const cistern = await api('/cistern');
  if (cistern.id) {
    const form = $('#cisternForm');
    form.name.value = cistern.name;
    form.capacityLiters.value = cistern.capacityLiters;
    form.currentLiters.value = cistern.currentLiters;
    form.minThreshold.value = cistern.minThreshold;
    form.maxThreshold.value = cistern.maxThreshold || '';
  }
  const readings = await api('/water-readings');
  renderTable('#readingsTable', readings, [
    {label:'Fecha', render:r => new Date(r.createdAt).toLocaleString()}, {label:'Litros', key:'liters'}, {label:'Fuente', key:'source'}, {label:'Observación', key:'observation'}
  ]);
}

async function loadHouses() {
  const houses = await api('/houses');
  $$('.housesSelect').forEach(select => {
    select.innerHTML = '<option value="">Seleccione vivienda</option>' + houses.map(h => `<option value="${h.id}">${h.houseNumber} - ${h.ownerName}</option>`).join('');
  });

  const consumptionHouseSelect = document.querySelector('#consumptionForm select[name="houseId"]');
  if (consumptionHouseSelect && !consumptionHouseSelect.dataset.calendarListenerAttached) {
    consumptionHouseSelect.addEventListener('change', () => {
      loadConsumptions(consumptionHouseSelect.value);
    });
    consumptionHouseSelect.dataset.calendarListenerAttached = 'true';
  }

  renderTable('#housesTable', houses, [
    {label:'Casa', key:'houseNumber'}, {label:'Propietario', key:'ownerName'}, {label:'Dirección', key:'address'}, {label:'Habitantes', key:'residentsCount'}, {label:'Estado', key:'status'}
  ]);
  const residents = await api('/residents');
  renderTable('#residentsTable', residents, [
    {label:'Vivienda ID', key:'houseId'}, {label:'Nombre', render:r => `${r.firstName} ${r.lastName}`}, {label:'Identificación', key:'identification'}, {label:'Menor', render:r => r.isMinor ? 'Sí' : 'No'}
  ]);
}

async function loadConsumptions(houseId = '') {
  const rows = await api(`/consumptions${houseId ? `?houseId=${houseId}` : ''}`);
  renderTable('#consumptionsTable', rows, [
    {label:'Casa', key:'houseNumber'}, {label:'Período', key:'period'}, {label:'Litros', key:'liters'}, {label:'Anomalía', render:r => r.isAnomalous ? '<span class="badge danger">Sí</span>' : '<span class="badge ok">No</span>'}, {label:'Observación', key:'observation'}
  ]);
  renderConsumptionCalendar(rows, houseId);
}

async function loadPayments() {
  const rows = await api('/payments');
  renderTable('#paymentsTable', rows, [
    {label:'Casa', key:'houseNumber'}, {label:'Período', key:'period'}, {label:'Monto', render:r => `Q ${Number(r.amount).toFixed(2)}`}, {label:'Recibo', key:'receiptNumber'}
  ]);
}

async function loadDistribution() {
  const rows = await api('/distribution-plans');
  renderTable('#distributionTable', rows, [
    {label:'Fecha', key:'serviceDate'}, {label:'Inicio', key:'startTime'}, {label:'Fin', key:'endTime'}, {label:'Notas', key:'notes'}
  ]);
}

async function loadMaintenance() {
  const rows = await api('/maintenance-orders');
  renderTable('#maintenanceTable', rows, [
    {label:'Fecha', key:'orderDate'}, {label:'Tipo', key:'maintenanceType'}, {label:'Responsable', key:'responsible'}, {label:'Estado', render:r => `<span class="badge ${r.status === 'finalizada' ? 'ok' : 'warn'}">${r.status}</span>`}, {label:'Descripción', key:'description'}
  ]);
  $('#ordersSelect').innerHTML = '<option value="">Seleccione orden</option>' + rows.map(o => `<option value="${o.id}">#${o.id} - ${o.maintenanceType} (${o.status})</option>`).join('');
}

async function loadNotifications() {
  const rows = await api('/notifications');
  $('#notificationsList').innerHTML = renderNotifications(rows, { hideRead: true, showMarkRead: state.user?.role !== 'cliente' });
}

async function loadUsers() {
  const rows = await api('/users');
  renderTable('#usersTable', rows, [
    {label:'Nombre', render:u => `${u.firstName} ${u.lastName}`},
    {label:'DPI', key:'dpi'},
    {label:'Dirección', key:'address'},
    {label:'Rol', render:u => `<span class="badge">${u.role}</span>`},
    {label:'Estado', render:u => u.isBlocked ? '<span class="badge danger">Bloqueado</span>' : '<span class="badge ok">Activo</span>'}
  ]);
}

async function markNotificationAsRead(notificationId) {
  await api(`/notifications/${notificationId}/read`, { method: 'POST' });
  await Promise.all([loadNotifications(), loadDashboard()]);
}

async function loadAll() {
  try {
    const role = state.user?.role;
    const tasks = [loadNotifications()];
    if (role === 'cliente') {
      tasks.push(loadDistribution(), loadMaintenance());
    } else if (role === 'soporte') {
      tasks.push(loadDashboard(), loadMaintenance());
    } else if (role === 'empleado') {
      tasks.push(loadDashboard(), loadHouses(), loadPayments());
    } else {
      tasks.push(loadDashboard(), loadCistern(), loadHouses(), loadConsumptions(), loadPayments(), loadDistribution(), loadMaintenance(), loadUsers());
    }
    await Promise.all(tasks);
  } catch (err) {
    toast(err.message, true);
    if (err.message.includes('token') || err.message.includes('autenticado')) logout();
  }
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  state.token = null; state.user = null;
  setAuthVisible();
}

function bindForm(selector, path, method, after) {
  $(selector).addEventListener('submit', async (e) => {
    e.preventDefault();
    const form = e.currentTarget;

    try {
      await api(path, { method, body: JSON.stringify(formData(form)) });
      form.reset();
      toast('Operación realizada correctamente');
      await after?.();
      await loadDashboard();
    } catch (err) {
      toast(err.message, true);
    }
  });
}

$('#loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const data = await api('/auth/login', { method:'POST', body: JSON.stringify(formData(e.currentTarget)) });
    state.token = data.token; state.user = data.user;
    localStorage.setItem('token', data.token); localStorage.setItem('user', JSON.stringify(data.user));
    setAuthVisible();
  } catch (err) { toast(err.message, true); }
});

$$('.nav-btn').forEach(btn => btn.addEventListener('click', () => {
  $$('.nav-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  $$('.view-section').forEach(s => s.classList.add('hidden'));
  const targetSection = $(`#${btn.dataset.view}`);
  if (targetSection) targetSection.classList.remove('hidden');
  const pageTitle = $('#pageTitle');
  if (pageTitle) pageTitle.textContent = btn.textContent;
  state.activeView = btn.dataset.view;
}));

$('#logoutBtn').addEventListener('click', logout);
$('#refreshBtn').addEventListener('click', loadAll);

document.addEventListener('click', async (event) => {
  const button = event.target.closest('.mark-read-btn');
  if (!button) return;
  const notificationId = button.dataset.id;
  if (!notificationId) return;

  try {
    await markNotificationAsRead(notificationId);
    toast('Notificación marcada como leída');
  } catch (err) {
    toast(err.message, true);
  }
});

$('#checkDelinquencyBtn').addEventListener('click', async () => {
  try {
    const rows = await api('/delinquency?period=2026-03&period=2026-04');
    renderTable('#delinquencyTable', rows, [
      {label:'Casa', key:'houseNumber'}, {label:'Propietario', key:'ownerName'}, {label:'Estado', render:() => '<span class="badge danger">Moroso</span>'}
    ]);
  } catch (err) { toast(err.message, true); }
});

bindForm('#cisternForm', '/cistern', 'POST', loadCistern);
bindForm('#sensorForm', '/sensor', 'POST', loadCistern);
bindForm('#houseForm', '/houses', 'POST', loadHouses);
bindForm('#residentForm', '/residents', 'POST', loadHouses);
bindForm('#consumptionForm', '/consumptions', 'POST', () => {
  const houseId = document.querySelector('#consumptionForm select[name="houseId"]').value;
  return loadConsumptions(houseId);
});
bindForm('#paymentForm', '/payments', 'POST', loadPayments);
bindForm('#distributionForm', '/distribution-plans', 'POST', loadDistribution);
bindForm('#maintenanceForm', '/maintenance-orders', 'POST', loadMaintenance);
bindForm('#interventionForm', '/maintenance-interventions', 'POST', loadMaintenance);
bindForm('#userForm', '/users', 'POST', loadUsers);

setAuthVisible();
decorateViewHeaders();
