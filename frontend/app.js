if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(console.error);
}

const API_BASE = '';



let currentLanguage = 'my';
let activeProjectId = null;
let activeJobPoller = null;

const i18nDict = {
  my: {
    auth_success: 'အောင်မြင်စွာ ဝင်ရောက်ပြီးပါပြီ။',
    key_saved: 'API သော့များကို သိမ်းဆည်းပြီးပါပြီ။',
    uploading: 'ဗီဒီယိုဖိုင် တင်သွင်းနေသည်...',
    upload_success: 'ဗီဒီယိုဖိုင် တင်သွင်းမှု အောင်မြင်ပါသည်။'
  },
  en: {
    auth_success: 'Logged in successfully.',
    key_saved: 'API keys securely stored.',
    uploading: 'Uploading video media...',
    upload_success: 'Video upload completed.'
  }
};

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 3500);
}

function setLanguage(lang) {
  currentLanguage = lang;
  document.documentElement.lang = lang;
  document.querySelectorAll('.i18n').forEach((el) => {
    const text = el.getAttribute(`data-${lang}`);
    if (text) el.textContent = text;
  });
  document.getElementById('lang-toggle-btn').textContent = lang === 'my' ? '🇲🇲 MY' : '🇺🇸 EN';
}

document.getElementById('lang-toggle-btn').addEventListener('click', () => {
  setLanguage(currentLanguage === 'my' ? 'en' : 'my');
});

document.getElementById('theme-toggle-btn').addEventListener('click', () => {
  const doc = document.documentElement;
  doc.setAttribute('data-theme', doc.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
});

function switchView(viewId) {
  document.querySelectorAll('.view').forEach((v) => v.classList.add('hidden'));
  document.getElementById(viewId).classList.remove('hidden');
  document.querySelectorAll('.nav-item').forEach((n) => {
    n.classList.toggle('active', n.getAttribute('data-target') === viewId);
  });
}

document.querySelectorAll('.nav-item').forEach((btn) => {
  btn.addEventListener('click', () => switchView(btn.getAttribute('data-target')));
});

let isRegisterMode = false;
document.getElementById('toggle-auth-mode').addEventListener('click', (e) => {
  e.preventDefault();
  isRegisterMode = !isRegisterMode;
  document.getElementById('invite-group').classList.toggle('hidden', !isRegisterMode);
  document.getElementById('auth-submit-btn').textContent = isRegisterMode ? 'Register' : 'Login';
});

document.getElementById('auth-submit-btn').addEventListener('click', async () => {
  const email = document.getElementById('auth-email').value;
  const password = document.getElementById('auth-password').value;
  const invite = document.getElementById('auth-invite').value;

  const endpoint = isRegisterMode ? '/api/auth/register' : '/api/auth/login';
  const payload = isRegisterMode ? { email, password, invite_code: invite } : { email, password };

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Authentication failed');

    if (!isRegisterMode && data.access_token) {
      localStorage.setItem('token', data.access_token);
      showToast(i18nDict[currentLanguage].auth_success);
      document.getElementById('logout-btn').style.display = 'block';
      loadProjects();
      switchView('dashboard-view');
    } else {
      showToast('Registration successful! Please login.');
      document.getElementById('toggle-auth-mode').click();
    }
  } catch (err) {
    showToast(err.message);
  }
});

async function loadProjects() {
  const token = localStorage.getItem('token');
  if (!token) return switchView('auth-view');

  try {
    const res = await fetch(`${API_BASE}/api/projects/`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.status === 401) return switchView('auth-view');
    const projects = await res.json();

    const list = document.getElementById('projects-list');
    list.innerHTML = '';
    projects.forEach((p) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <h3>${p.title}</h3>
        <p class="text-muted">Lang: ${p.target_language.toUpperCase()} | Ratio: ${p.aspect_ratio}</p>
        <span class="badge">${p.status}</span>
        <button class="btn btn-secondary w-full mt-2" onclick="openStudio('${p.id}')">Open Studio</button>
      `;
      list.appendChild(card);
    });
  } catch (e) {
    console.error(e);
  }
}

window.openStudio = async function(id) {
  activeProjectId = id;
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}/api/projects/${id}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const p = await res.json();
  document.getElementById('current-project-title').textContent = p.title;
  document.getElementById('current-status-badge').textContent = p.status;
  document.getElementById('proj-script-text').value = p.script_text || '';
  switchView('studio-view');
};

document.getElementById('back-to-dash-btn').addEventListener('click', () => {
  switchView('dashboard-view');
});

document.getElementById('upload-video-btn').addEventListener('click', async () => {
  const picker = document.getElementById('video-file-picker');
  if (!picker.files.length) return showToast('Please select a video file first.');

  const file = picker.files[0];
  const formData = new FormData();
  formData.append('file', file);

  const token = localStorage.getItem('token');
  const pBox = document.getElementById('upload-progress-container');
  const pBar = document.getElementById('upload-progress-bar');
  const pText = document.getElementById('upload-progress-text');
  pBox.classList.remove('hidden');

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `${API_BASE}/api/projects/${activeProjectId}/upload-video`);
  xhr.setRequestHeader('Authorization', `Bearer ${token}`);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      pBar.style.width = `${percent}%`;
      pText.textContent = `${percent}%`;
    }
  };

  xhr.onload = () => {
    pBox.classList.add('hidden');
    if (xhr.status === 200) {
      showToast(i18nDict[currentLanguage].upload_success);
    } else {
      showToast(`Upload failed: ${xhr.responseText}`);
    }
  };
  xhr.send(formData);
});

document.getElementById('start-render-btn').addEventListener('click', async () => {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}/api/jobs/render/${activeProjectId}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  });
  const job = await res.json();
  if (res.ok) {
    trackJobProgress(job.id);
  } else {
    showToast(job.detail || 'Could not queue render.');
  }
});

function trackJobProgress(jobId) {
  const box = document.getElementById('render-job-status');
  const pBar = document.getElementById('render-progress-bar');
  const stage = document.getElementById('job-stage-text');
  const pct = document.getElementById('job-percent-text');
  box.classList.remove('hidden');

  if (activeJobPoller) clearInterval(activeJobPoller);

  activeJobPoller = setInterval(async () => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    const job = await res.json();

    pBar.style.width = `${job.progress}%`;
    pct.textContent = `${job.progress}%`;
    stage.textContent = `Stage: ${job.stage}`;

    if (job.status === 'COMPLETED') {
      clearInterval(activeJobPoller);
      showToast('Recap render completed!');
      document.getElementById('download-actions').classList.remove('hidden');
      document.getElementById('download-video-btn').href = `${API_BASE}/api/media/download/${activeProjectId}/video`;
      document.getElementById('download-srt-btn').href = `${API_BASE}/api/media/download/${activeProjectId}/subtitles`;
    } else if (job.status === 'FAILED') {
      clearInterval(activeJobPoller);
      showToast(`Job failed: ${job.error_message}`);
    }
  }, 3000);
}

if (localStorage.getItem('token')) {
  loadProjects();
  switchView('dashboard-view');
} else {
  switchView('auth-view');
}
// New Project Button Handler
document.getElementById('open-new-project-btn')?.addEventListener('click', async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    showToast('ကျေးဇူးပြု၍ အရင်ဆုံး Login ဝင်ပါ');
    return switchView('auth-view');
  }

  const title = prompt('Project အမည် ရိုက်ထည့်ပါ:');
  if (!title || !title.trim()) return;

  try {
    const res = await fetch(`${API_BASE}/api/projects/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        title: title.trim(),
        target_language: 'my',
        aspect_ratio: '16:9',
        target_duration_minutes: 3,
        burn_subtitles: true,
        voice_name: 'my-MM-ThihaNeural'
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Project ဖန်တီး၍ မရပါ');

    showToast('Project အသစ် ဖန်တီးပြီးပါပြီ');
    loadProjects();
    openStudio(data.id);
  } catch (err) {
    showToast(err.message);
  }
});
let ffmpegInstance = null;
async function loadFFmpeg() {
  if (ffmpegInstance) return ffmpegInstance;
  const { createFFmpeg } = FFmpeg;
  ffmpegInstance = createFFmpeg({
    log: true,
    corePath: 'https://unpkg.com/@ffmpeg/core@0.11.0/dist/ffmpeg-core.js'
  });
  await ffmpegInstance.load();
  return ffmpegInstance;
}

document.getElementById('device-render-btn')?.addEventListener('click', async () => {
  const fileInput = document.getElementById('local-video-input');
  const videoFile = fileInput?.files[0];
  if (!videoFile) return alert('ဗီဒီယိုဖိုင်ကို အရင်ရွေးချယ်ပါ');

  const pBox = document.getElementById('render-progress-box');
  const sText = document.getElementById('render-status-text');
  const pText = document.getElementById('render-percent');
  const pBar = document.getElementById('render-progress-bar');
  const dBox = document.getElementById('download-result-box');
  const dLink = document.getElementById('download-final-video');

  try {
    pBox.style.display = 'block';
    dBox.style.display = 'none';
    sText.innerText = 'FFmpeg စတင်နေပါသည်...';

    const ffmpeg = await loadFFmpeg();
    ffmpeg.setProgress(({ ratio }) => {
      const p = Math.max(0, Math.min(100, Math.round(ratio * 100)));
      pBar.style.width = `${p}%`;
      pText.innerText = `${p}%`;
    });

    sText.innerText = 'ဗီဒီယို ထည့်သွင်းနေပါသည်...';
    const { fetchFile } = FFmpeg;
    ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(videoFile));

    sText.innerText = 'ဗီဒီယို အချောသတ် Render လုပ်နေပါသည်...';
    await ffmpeg.run('-i', 'input.mp4', '-c', 'copy', 'output.mp4');

    const data = ffmpeg.FS('readFile', 'output.mp4');
    const blob = new Blob([data.buffer], { type: 'video/mp4' });
    dLink.href = URL.createObjectURL(blob);
    dLink.download = `Recap_${Date.now()}.mp4`;
    dBox.style.display = 'block';
    sText.innerText = 'ပြီးစီးပါပြီ!';

    ffmpeg.FS('unlink', 'input.mp4');
    ffmpeg.FS('unlink', 'output.mp4');
  } catch (err) {
    alert('Error: ' + err.message);
  }
});
