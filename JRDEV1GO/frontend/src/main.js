import './style.css';

// Wails runtime e bindings
const go = window['go']?.['main']?.['App'] || {};

const CheckLicense       = () => go['CheckLicense']?.() || Promise.resolve({code:'not_found'});
const ActivateLicense    = (k) => go['ActivateLicense']?.(k) || Promise.resolve({success:false,message:'Erro'});
const GetLicenseInfo     = () => go['GetLicenseInfo']?.() || Promise.resolve({});
const GetSystemInfo      = () => go['GetSystemInfo']?.() || Promise.resolve({});
const GetNetworkInterfaces = () => go['GetNetworkInterfaces']?.() || Promise.resolve([]);
const StartPXE           = (ip,mask,wd) => go['StartPXE']?.(ip,mask,wd) || Promise.resolve({success:false});
const StopPXE            = () => go['StopPXE']?.() || Promise.resolve();
const GetPXELogs         = () => go['GetPXELogs']?.() || Promise.resolve([]);
const IsPXERunning       = () => go['IsPXERunning']?.() || Promise.resolve(false);
const ExtractISO         = (a,b) => go['ExtractISO']?.(a,b) || Promise.resolve({success:false});
const BuildISO           = (a,b,c) => go['BuildISO']?.(a,b,c) || Promise.resolve({success:false});
const MountWIM           = (a,b) => go['MountWIM']?.(a,b) || Promise.resolve({success:false});
const UnmountWIM         = (a,b) => go['UnmountWIM']?.(a,b) || Promise.resolve({success:false});
const InjectDrivers      = (a,b) => go['InjectDrivers']?.(a,b) || Promise.resolve({success:false});
const GetWorkspaceDir    = () => go['GetWorkspaceDir']?.() || Promise.resolve('E:\\WinPE_Studio_Workspace');

// ── Estado global ─────────────────────────────────────────────────────────
const state = {
  page: 'dashboard',
  pxeRunning: false,
  wimMounted: false,
  workDir: '',
  licInfo: null,
  logInterval: null,
};

// ── Init ──────────────────────────────────────────────────────────────────
// Aguarda o runtime Wails estar pronto antes de iniciar
window.addEventListener('load', () => {
  // Wails injeta window.go após o DOM carregar — aguarda até 3s
  let attempts = 0;
  const waitForWails = setInterval(() => {
    attempts++;
    if (window['go']?.['main']?.['App'] || attempts > 30) {
      clearInterval(waitForWails);
      checkLicense();
    }
  }, 100);
});

async function checkLicense() {
  const status = await CheckLicense();
  if (status.code === 'valid') {
    state.licInfo = await GetLicenseInfo();
    initApp();
  } else {
    showActivation(status);
  }
}

// ── Tela de Ativação ──────────────────────────────────────────────────────
function showActivation(status) {
  const msgs = {
    not_found: '⚠️ Nenhuma licença encontrada. Insira sua chave.',
    expired:   '🔴 Licença expirada. Entre em contato para renovar.',
    wrong_mac: '🔴 Esta licença pertence a outro computador.',
    invalid:   '🔴 Licença inválida ou corrompida.',
  };

  document.getElementById('app').innerHTML = `
    <div id="activation-screen">
      <div class="activation-box">
        <div class="logo">💡</div>
        <div class="title">JRDEV1 PXE</div>
        <div class="sub">WinPE Studio Pro — Ativação de Licença</div>
        <div style="background:var(--card2);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:20px;font-size:12px;color:var(--orange)">
          ${msgs[status.code] || '⚠️ Ativação necessária.'}
        </div>
        <div class="form-row">
          <label class="form-label">Chave de Licença</label>
          <input id="key-input" class="key-input" placeholder="KIRO-XXXX-XXXX-XXXX-XXXX" maxlength="24" />
        </div>
        <div class="activation-error" id="act-error"></div>
        <button class="btn btn-primary" style="width:100%;margin-top:12px;padding:12px" onclick="doActivate()">
          🔑 Ativar Licença
        </button>
        <div style="font-size:11px;color:var(--text3);margin-top:16px">
          Precisa de uma licença? Entre em contato com o suporte.
        </div>
      </div>
    </div>`;

  // Auto-formata a chave
  document.getElementById('key-input').addEventListener('input', (e) => {
    let v = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (v.startsWith('KIRO')) v = v.slice(4);
    const parts = [];
    for (let i = 0; i < Math.min(v.length, 16); i += 4) parts.push(v.slice(i, i+4));
    e.target.value = 'KIRO-' + parts.join('-');
  });

  document.getElementById('key-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doActivate();
  });
}

window.doActivate = async function() {
  const key = document.getElementById('key-input').value.trim();
  const errEl = document.getElementById('act-error');
  errEl.textContent = '';

  const result = await ActivateLicense(key);
  if (result.success) {
    state.licInfo = await GetLicenseInfo();
    initApp();
  } else {
    errEl.textContent = result.message;
  }
};

// ── App Principal ─────────────────────────────────────────────────────────
function initApp() {
  document.getElementById('app').innerHTML = buildLayout();
  bindNav();
  navigate('dashboard');
  updateLicenseBadge();
  loadDashboard();
}

function buildLayout() {
  return `
    <div class="sidebar">
      <div class="sidebar-logo">
        <div class="icon">💡</div>
        <div class="brand">JRDEV1 PXE</div>
        <div class="tagline">WinPE Studio Pro</div>
      </div>
      <nav class="nav">
        ${navBtn('dashboard', '🏠', 'Início')}
        ${navBtn('prepare',   '📀', 'Preparar ISO')}
        ${navBtn('pxe',       '📡', 'Rede PXE')}
        ${navBtn('iso',       '⚙️',  'Gerar ISO')}
        ${navBtn('custom',    '🎨', 'Customizar')}
        ${navBtn('logs',      '📋', 'Logs')}
        ${navBtn('about',     'ℹ️',  'Sobre')}
      </nav>
      <div class="sidebar-footer">
        <div id="iso-loaded" style="font-size:11px;color:var(--text3);text-align:center;padding:4px 8px;margin-bottom:6px">Nenhuma ISO</div>
        <div class="license-badge" id="lic-badge">🔑 Carregando...</div>
        <button class="btn-exit" onclick="confirmExit()">⏻ Fechar</button>
      </div>
    </div>
    <div class="content">
      <div class="progress-bar"><div class="fill" id="progress-fill"></div></div>
      <div id="page-dashboard" class="page">${pageDashboard()}</div>
      <div id="page-prepare"   class="page">${pagePrepare()}</div>
      <div id="page-pxe"       class="page">${pagePXE()}</div>
      <div id="page-iso"       class="page">${pageISO()}</div>
      <div id="page-custom"    class="page">${pageCustom()}</div>
      <div id="page-logs"      class="page">${pageLogs()}</div>
      <div id="page-about"     class="page">${pageAbout()}</div>
    </div>`;
}

function navBtn(id, icon, label) {
  return `<button class="nav-btn" data-page="${id}" onclick="navigate('${id}')">
    <span class="nav-icon">${icon}</span>${label}
  </button>`;
}

function bindNav() {}

window.navigate = function(page) {
  state.page = page;
  document.querySelectorAll('.nav-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.page === page);
  });
  document.querySelectorAll('.page').forEach(p => {
    p.classList.toggle('active', p.id === 'page-' + page);
  });
  if (page === 'dashboard') loadDashboard();
  if (page === 'prepare')   loadPreparePage();
  if (page === 'pxe')       loadPXEPage();
  if (page === 'logs')      startLogPolling();
  else stopLogPolling();
};

// ── Dashboard ─────────────────────────────────────────────────────────────
function pageDashboard() {
  return `
    <div class="page-title">🏠 Início</div>
    <div class="page-sub">Status do sistema e ações rápidas</div>
    <div class="card-grid" id="dash-cards">
      <div class="stat-card"><div class="label">DISM</div><div class="value" id="d-dism">...</div></div>
      <div class="stat-card"><div class="label">7-Zip</div><div class="value" id="d-7z">...</div></div>
      <div class="stat-card"><div class="label">oscdimg</div><div class="value" id="d-osc">...</div></div>
      <div class="stat-card"><div class="label">Espaço Livre (E:)</div><div class="value" id="d-space">...</div></div>
    </div>
    <div class="group">
      <div class="group-title">⚡ Ações Rápidas</div>
      <div class="group-body">
        <div style="background:var(--card2);border:1px solid var(--accent);border-radius:8px;padding:16px;margin-bottom:14px">
          <div style="font-size:13px;font-weight:700;color:var(--accent);margin-bottom:6px">🚀 Fluxo Principal</div>
          <div style="font-size:12px;color:var(--text3);margin-bottom:12px">
            1. Selecione uma ISO → 2. Extraia → 3. Inicie o PXE → 4. Dê boot nos notebooks
          </div>
          <button class="btn btn-primary" style="width:100%;padding:12px;font-size:14px" onclick="navigate('prepare')">
            📀 Preparar ISO para PXE →
          </button>
        </div>
        <div class="btn-row">
          <button class="btn" onclick="navigate('pxe')">📡 Servidor PXE</button>
          <button class="btn" onclick="navigate('custom')">🎨 Customizar WIM</button>
          <button class="btn" onclick="navigate('iso')">⚙️ Gerar ISO</button>
        </div>
      </div>
    </div>`;
}

async function loadDashboard() {
  const info = await GetSystemInfo();
  const set = (id, val, ok) => {
    const el = document.getElementById(id);
    if (el) { el.textContent = val; el.className = 'value ' + (ok ? 'ok' : 'err'); }
  };
  set('d-dism',  info.dism_found ? '✅ OK' : '❌ Não encontrado', info.dism_found);
  set('d-7z',    info.seven_zip  ? '✅ OK' : '❌ Não encontrado', !!info.seven_zip);
  set('d-osc',   info.oscdimg    ? '✅ OK' : '❌ Não encontrado', !!info.oscdimg);
  set('d-space', info.free_space_gb.toFixed(1) + ' GB',
      info.free_space_gb > 10);
}

// ── Preparar ISO Page ─────────────────────────────────────────────────────
function pagePrepare() {
  return `
    <div class="page-title">📀 Preparar ISO para PXE</div>
    <div class="page-sub">Selecione uma ISO, extraia e prepare para boot via rede</div>

    <div class="group">
      <div class="group-title">1️⃣ Selecionar ISO</div>
      <div class="group-body">
        <div class="form-row">
          <label class="form-label">Caminho da ISO (WinPE, Strelec, Hiren's, etc.)</label>
          <div style="display:flex;gap:8px">
            <input id="prep-iso" placeholder="E:\\imagem.iso" style="flex:1" />
            <button class="btn" onclick="browseISO()">📂 Procurar</button>
          </div>
        </div>
        <div class="form-row">
          <label class="form-label">Pasta de Destino (onde extrair)</label>
          <div style="display:flex;gap:8px">
            <input id="prep-dest" placeholder="E:\\WinPE_Studio_Workspace\\PROJETO" style="flex:1" />
            <button class="btn" onclick="autoFillDest()">🔄 Auto</button>
          </div>
        </div>
      </div>
    </div>

    <div class="group">
      <div class="group-title">2️⃣ Extrair e Preparar</div>
      <div class="group-body">
        <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
          <div id="prep-status" style="flex:1;padding:10px;background:var(--card2);border:1px solid var(--border);border-radius:8px;font-size:12px;color:var(--text3)">
            Aguardando seleção da ISO...
          </div>
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" id="btn-extract" onclick="doExtractForPXE()" disabled>
            📦 Extrair ISO
          </button>
          <button class="btn" id="btn-inject-net" onclick="doInjectNetDrivers()" disabled>
            🔌 Injetar Drivers de Rede
          </button>
        </div>
      </div>
    </div>

    <div class="group">
      <div class="group-title">3️⃣ Iniciar PXE</div>
      <div class="group-body">
        <div style="font-size:12px;color:var(--text3);margin-bottom:12px">
          Após extrair a ISO, configure e inicie o servidor PXE para os notebooks darem boot.
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" id="btn-go-pxe" onclick="goToPXEWithProject()" disabled>
            📡 Ir para Rede PXE →
          </button>
        </div>
      </div>
    </div>

    <div class="group">
      <div class="group-title">📋 Log de Preparação</div>
      <div class="group-body">
        <div class="log-area" id="prep-log" style="height:200px"></div>
      </div>
    </div>`;
}

async function loadPreparePage() {
  const wd = await GetWorkspaceDir();
  const destEl = document.getElementById('prep-dest');
  if (destEl && !destEl.value) {
    const ts = new Date().toTimeString().slice(0,8).replace(/:/g,'');
    destEl.value = wd + '\\PROJETO_' + ts;
  }
  // Habilita botão extrair se ISO já preenchida
  checkPrepReady();
}

window.browseISO = async function() {
  // Usa diálogo nativo do Wails
  const iso = await (window['go']?.['main']?.['App']?.['BrowseISO']?.() || Promise.resolve(''));
  if (iso) {
    document.getElementById('prep-iso').value = iso;
    const name = iso.split('\\').pop().replace(/\.iso$/i,'');
    const ts = new Date().toTimeString().slice(0,8).replace(/:/g,'');
    document.getElementById('prep-dest').value =
      `E:\\WinPE_Studio_Workspace\\${name}_${ts}`;
    checkPrepReady();
  }
};

window.autoFillDest = async function() {
  const iso = document.getElementById('prep-iso').value;
  const wd  = await GetWorkspaceDir();
  const name = iso ? iso.split('\\').pop().replace(/\.iso$/i,'') : 'PROJETO';
  const ts = new Date().toTimeString().slice(0,8).replace(/:/g,'');
  document.getElementById('prep-dest').value = `${wd}\\${name}_${ts}`;
  checkPrepReady();
};

function checkPrepReady() {
  const iso  = document.getElementById('prep-iso')?.value;
  const dest = document.getElementById('prep-dest')?.value;
  const btn  = document.getElementById('btn-extract');
  if (btn) btn.disabled = !(iso && dest);
}

function prepLog(msg, type = '') {
  const el = document.getElementById('prep-log');
  if (!el) return;
  const ts = new Date().toTimeString().slice(0,8);
  const cls = type === 'ok' ? 'log-ok' : type === 'err' ? 'log-err' : type === 'warn' ? 'log-warn' : '';
  el.innerHTML += `<span class="${cls}">[${ts}] ${msg}</span>\n`;
  el.scrollTop = el.scrollHeight;
}

window.doExtractForPXE = async function() {
  const iso  = document.getElementById('prep-iso').value.trim();
  const dest = document.getElementById('prep-dest').value.trim();
  if (!iso || !dest) return;

  const btn = document.getElementById('btn-extract');
  btn.disabled = true;
  btn.textContent = '⏳ Extraindo...';

  setProgress(10);
  prepLog(`Extraindo: ${iso}`);
  prepLog(`Destino: ${dest}`);

  document.getElementById('prep-status').innerHTML =
    '<span style="color:var(--orange)">⏳ Extraindo ISO... aguarde (pode demorar alguns minutos)</span>';

  const r = await ExtractISO(iso, dest);
  setProgress(70);

  if (r.success) {
    state.workDir = dest;
    prepLog('✅ ISO extraída com sucesso!', 'ok');
    prepLog(`Projeto: ${dest}`, 'ok');

    document.getElementById('prep-status').innerHTML =
      `<span style="color:var(--green)">✅ ISO extraída em: ${dest}</span>`;

    // Atualiza sidebar
    const isoName = iso.split('\\').pop();
    const sideEl = document.getElementById('iso-loaded');
    if (sideEl) sideEl.textContent = '📀 ' + isoName;

    // Habilita próximos passos
    document.getElementById('btn-inject-net').disabled = false;
    document.getElementById('btn-go-pxe').disabled = false;

    // Preenche campos das outras páginas
    const wimPath = dest + '\\sources\\boot.wim';
    const mountDir = dest + '_Mount';
    const wdEl = document.getElementById('pxe-workdir');
    if (wdEl) wdEl.value = dest;
    const wimEl = document.getElementById('wim-path');
    if (wimEl) wimEl.value = wimPath;
    const mountEl = document.getElementById('wim-mount');
    if (mountEl) mountEl.value = mountDir;
    const buildSrc = document.getElementById('build-src');
    if (buildSrc) buildSrc.value = dest;

    prepLog('💡 Próximo passo: Injetar Drivers de Rede ou ir direto para PXE', 'warn');
  } else {
    prepLog('❌ Erro na extração: ' + r.error, 'err');
    document.getElementById('prep-status').innerHTML =
      `<span style="color:var(--red)">❌ Erro: ${r.error}</span>`;
  }

  setProgress(0);
  btn.disabled = false;
  btn.textContent = '📦 Extrair ISO';
};

window.doInjectNetDrivers = async function() {
  if (!state.workDir) {
    prepLog('❌ Extraia a ISO primeiro', 'err');
    return;
  }
  const wimPath  = state.workDir + '\\sources\\boot.wim';
  const mountDir = state.workDir + '_Mount_Net';

  prepLog('🔌 Iniciando injeção de drivers de rede...', 'warn');
  setProgress(20);

  // Monta WIM
  prepLog(`Montando: ${wimPath}`);
  const mnt = await MountWIM(wimPath, mountDir);
  if (!mnt.success) {
    prepLog('❌ Falha ao montar WIM: ' + mnt.error, 'err');
    setProgress(0);
    return;
  }
  prepLog('✅ WIM montado', 'ok');
  setProgress(50);

  // Injeta drivers LAN da pasta resources
  const driverDir = 'drivers'; // relativo ao exe
  prepLog('💉 Injetando drivers LAN...');
  const inj = await InjectDrivers(mountDir, driverDir);
  setProgress(80);

  // Desmonta e salva
  prepLog('💾 Salvando WIM...');
  const unm = await UnmountWIM(mountDir, true);
  setProgress(100);

  if (unm.success) {
    prepLog('✅ Drivers de rede injetados com sucesso!', 'ok');
  } else {
    prepLog('⚠️ Aviso ao desmontar: ' + unm.error, 'warn');
  }
  setProgress(0);
};

window.goToPXEWithProject = function() {
  if (state.workDir) {
    const wdEl = document.getElementById('pxe-workdir');
    if (wdEl) wdEl.value = state.workDir;
  }
  navigate('pxe');
};

function setProgress(pct) {
  const el = document.getElementById('progress-fill');
  if (el) el.style.width = pct + '%';
}

// ── PXE Page ──────────────────────────────────────────────────────────────
function pagePXE() {
  return `
    <div class="page-title">📡 Servidor PXE</div>
    <div class="page-sub">DHCP + TFTP + HTTP para boot via rede</div>
    <div class="pxe-status">
      <div class="pxe-dot" id="pxe-dot"></div>
      <span id="pxe-status-text">Servidor parado</span>
    </div>
    <div class="group">
      <div class="group-title">Configuração</div>
      <div class="group-body">
        <div class="form-row">
          <label class="form-label">Interface de Rede</label>
          <select id="pxe-iface"></select>
        </div>
        <div class="form-row">
          <label class="form-label">Pasta do Projeto (WinPE extraído)</label>
          <input id="pxe-workdir" placeholder="E:\\WinPE_Studio_Workspace\\PROJETO" />
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" id="btn-pxe-start" onclick="togglePXE()">▶ Iniciar PXE</button>
        </div>
      </div>
    </div>
    <div class="group">
      <div class="group-title">Log do Servidor</div>
      <div class="group-body">
        <div class="log-area" id="pxe-log"></div>
      </div>
    </div>`;
}

async function loadPXEPage() {
  const ifaces = await GetNetworkInterfaces();
  const sel = document.getElementById('pxe-iface');
  if (sel) {
    sel.innerHTML = ifaces.map(i =>
      `<option value="${i.ip}|${i.mask}">${i.name} — ${i.ip}</option>`
    ).join('');
  }
  const wd = await GetWorkspaceDir();
  const wdEl = document.getElementById('pxe-workdir');
  if (wdEl && !wdEl.value) wdEl.value = wd;
  updatePXEStatus();
}

window.togglePXE = async function() {
  if (state.pxeRunning) {
    await StopPXE();
    state.pxeRunning = false;
    stopLogPolling();
  } else {
    const sel = document.getElementById('pxe-iface');
    const wd  = document.getElementById('pxe-workdir');
    if (!sel || !wd) return;
    const [ip, mask] = sel.value.split('|');
    const result = await StartPXE(ip, mask, wd.value);
    if (result.success) {
      state.pxeRunning = true;
      startLogPolling();
    } else {
      alert('Erro: ' + result.message);
    }
  }
  updatePXEStatus();
};

function updatePXEStatus() {
  const dot  = document.getElementById('pxe-dot');
  const text = document.getElementById('pxe-status-text');
  const btn  = document.getElementById('btn-pxe-start');
  if (!dot) return;
  if (state.pxeRunning) {
    dot.classList.add('on');
    if (text) text.textContent = 'Servidor rodando — aguardando clientes PXE';
    if (btn)  { btn.textContent = '⏹ Parar PXE'; btn.className = 'btn btn-danger'; }
  } else {
    dot.classList.remove('on');
    if (text) text.textContent = 'Servidor parado';
    if (btn)  { btn.textContent = '▶ Iniciar PXE'; btn.className = 'btn btn-primary'; }
  }
}

// ── ISO Page ──────────────────────────────────────────────────────────────
function pageISO() {
  return `
    <div class="page-title">💿 ISO / WIM</div>
    <div class="page-sub">Extrair ISO e gerar nova imagem bootável</div>
    <div class="group">
      <div class="group-title">Extrair ISO</div>
      <div class="group-body">
        <div class="form-row">
          <label class="form-label">Caminho da ISO</label>
          <input id="iso-path" placeholder="E:\\imagem.iso" />
        </div>
        <div class="form-row">
          <label class="form-label">Pasta de Destino</label>
          <input id="iso-dest" placeholder="E:\\WinPE_Studio_Workspace\\PROJETO" />
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" onclick="doExtractISO()">📦 Extrair ISO</button>
        </div>
      </div>
    </div>
    <div class="group">
      <div class="group-title">Gerar ISO</div>
      <div class="group-body">
        <div class="form-row">
          <label class="form-label">Pasta Fonte (WinPE editado)</label>
          <input id="build-src" placeholder="E:\\WinPE_Studio_Workspace\\PROJETO" />
        </div>
        <div class="form-row">
          <label class="form-label">ISO de Saída</label>
          <input id="build-out" placeholder="E:\\WINPE_FINAL.iso" />
        </div>
        <div class="form-row">
          <label class="form-label">Label do Volume</label>
          <input id="build-label" value="WINPE_STUDIO" />
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" onclick="doBuildISO()">⚙️ Gerar ISO</button>
        </div>
      </div>
    </div>
    <div class="log-area" id="iso-log" style="margin-top:16px"></div>`;
}

window.doExtractISO = async function() {
  const iso  = document.getElementById('iso-path').value;
  const dest = document.getElementById('iso-dest').value;
  const log  = document.getElementById('iso-log');
  log.textContent = 'Extraindo...';
  const r = await ExtractISO(iso, dest);
  log.textContent = r.success ? '✅ ' + r.output : '❌ ' + r.error;
};

window.doBuildISO = async function() {
  const src   = document.getElementById('build-src').value;
  const out   = document.getElementById('build-out').value;
  const label = document.getElementById('build-label').value;
  const log   = document.getElementById('iso-log');
  log.textContent = 'Gerando ISO...';
  const r = await BuildISO(src, out, label);
  log.textContent = r.success ? '✅ ISO gerada: ' + out : '❌ ' + r.error;
};

// ── Customizar Page ───────────────────────────────────────────────────────
function pageCustom() {
  return `
    <div class="page-title">🎨 Customizar WinPE</div>
    <div class="page-sub">Montar, editar e desmontar o boot.wim</div>
    <div class="group">
      <div class="group-title">Montar / Desmontar WIM</div>
      <div class="group-body">
        <div class="form-row">
          <label class="form-label">Caminho do boot.wim</label>
          <input id="wim-path" placeholder="E:\\WinPE_Studio_Workspace\\PROJETO\\sources\\boot.wim" />
        </div>
        <div class="form-row">
          <label class="form-label">Pasta de Montagem</label>
          <input id="wim-mount" placeholder="E:\\WinPE_Studio_Workspace\\Mount_PROJETO" />
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" onclick="doMountWIM()">🚀 Montar WIM</button>
          <button class="btn btn-success" onclick="doUnmountWIM(true)">💾 Salvar e Desmontar</button>
          <button class="btn btn-danger"  onclick="doUnmountWIM(false)">🗑️ Descartar e Desmontar</button>
        </div>
      </div>
    </div>
    <div class="group">
      <div class="group-title">Injetar Drivers</div>
      <div class="group-body">
        <div class="form-row">
          <label class="form-label">Pasta de Montagem</label>
          <input id="drv-mount" placeholder="E:\\WinPE_Studio_Workspace\\Mount_PROJETO" />
        </div>
        <div class="form-row">
          <label class="form-label">Pasta de Drivers (.inf)</label>
          <input id="drv-dir" placeholder="C:\\Drivers" />
        </div>
        <div class="btn-row">
          <button class="btn btn-primary" onclick="doInjectDrivers()">💉 Injetar Drivers</button>
        </div>
      </div>
    </div>
    <div class="log-area" id="custom-log" style="margin-top:16px"></div>`;
}

window.doMountWIM = async function() {
  const wim   = document.getElementById('wim-path').value;
  const mount = document.getElementById('wim-mount').value;
  const log   = document.getElementById('custom-log');
  log.textContent = 'Montando WIM...';
  const r = await MountWIM(wim, mount);
  log.textContent = r.success ? '✅ WIM montado em: ' + mount : '❌ ' + r.error;
};

window.doUnmountWIM = async function(commit) {
  const mount = document.getElementById('wim-mount').value;
  const log   = document.getElementById('custom-log');
  log.textContent = commit ? 'Salvando e desmontando...' : 'Descartando e desmontando...';
  const r = await UnmountWIM(mount, commit);
  log.textContent = r.success ? '✅ WIM desmontado' : '❌ ' + r.error;
};

window.doInjectDrivers = async function() {
  const mount = document.getElementById('drv-mount').value;
  const dir   = document.getElementById('drv-dir').value;
  const log   = document.getElementById('custom-log');
  log.textContent = 'Injetando drivers...';
  const r = await InjectDrivers(mount, dir);
  log.textContent = r.success ? '✅ Drivers injetados' : '❌ ' + r.error;
};

// ── Logs Page ─────────────────────────────────────────────────────────────
function pageLogs() {
  return `
    <div class="page-title">📋 Logs</div>
    <div class="page-sub">Log em tempo real do servidor PXE</div>
    <div class="btn-row" style="margin-bottom:12px">
      <button class="btn" onclick="clearLogs()">🗑️ Limpar</button>
    </div>
    <div class="log-area" id="main-log" style="height:calc(100vh - 200px)"></div>`;
}

function startLogPolling() {
  if (state.logInterval) return;
  state.logInterval = setInterval(async () => {
    const logs = await GetPXELogs();
    const el = document.getElementById('main-log') || document.getElementById('pxe-log');
    if (el && logs.length > 0) {
      el.textContent = logs.join('\n');
      el.scrollTop = el.scrollHeight;
    }
  }, 1000);
}

function stopLogPolling() {
  if (state.logInterval) {
    clearInterval(state.logInterval);
    state.logInterval = null;
  }
}

window.clearLogs = function() {
  const el = document.getElementById('main-log');
  if (el) el.textContent = '';
};

// ── About Page ────────────────────────────────────────────────────────────
function pageAbout() {
  return `
    <div class="about-banner">
      <div class="about-logo">💡</div>
      <div class="about-name">JRDEV1 PXE</div>
      <div class="about-sub">WinPE Studio Pro</div>
      <div class="about-ver">Versão 2.1.0 — Go Edition</div>
    </div>
    <div class="about-dev">
      <div class="about-dev-label">Desenvolvido por</div>
      <div class="about-dev-name">JRDEV1</div>
      <div class="about-dev-role">Software Developer • &lt;/&gt; Código 💡 Inovação</div>
      <div style="font-size:11px;color:var(--text3);margin-top:8px">
        Solução profissional para boot PXE, clonagem e customização de imagens WinPE
      </div>
      <button class="btn-instagram" onclick="openInstagram()">📸 @jrdev1</button>
    </div>
    <div class="group">
      <div class="group-title">Recursos</div>
      <div class="group-body">
        ${['📡 Servidor PXE/TFTP/DHCP integrado',
           '💾 Injeção de drivers corporativos (Dell/HP/Lenovo)',
           '🌐 Boot via rede com wimboot + HTTPDisk',
           '🎨 Customização completa do WinPE',
           '⚙️ Geração de ISO bootável UEFI + BIOS',
           '🔑 Sistema de licenciamento por hardware'].map(f =>
          `<div style="padding:6px 0;color:var(--text2)">${f}</div>`
        ).join('')}
      </div>
    </div>
    <div style="text-align:center;color:var(--text3);font-size:11px;margin-top:16px">
      © 2024–2026 JRDEV1 — Todos os direitos reservados
    </div>`;
}

window.openInstagram = function() {
  window.open('https://www.instagram.com/jrdev1', '_blank');
};

// ── License Badge ─────────────────────────────────────────────────────────
function updateLicenseBadge() {
  const el = document.getElementById('lic-badge');
  if (!el || !state.licInfo) return;
  const d = state.licInfo.days_left;
  if (state.licInfo.developer) {
    el.textContent = '🔑 Dev Mode';
    el.className = 'license-badge valid';
  } else if (d <= 7) {
    el.textContent = `🔴 ${d}d restantes`;
    el.className = 'license-badge expired';
  } else if (d <= 30) {
    el.textContent = `⚠️ ${d}d restantes`;
    el.className = 'license-badge expiring';
  } else {
    el.textContent = `✅ ${d}d restantes`;
    el.className = 'license-badge valid';
  }
}

// ── Exit ──────────────────────────────────────────────────────────────────
window.confirmExit = function() {
  if (state.pxeRunning) {
    if (!confirm('O servidor PXE está ativo. Deseja fechar mesmo assim?')) return;
    StopPXE();
  }
  window['go']?.['main']?.['App'] && window.runtime?.Quit();
  window.close();
};
