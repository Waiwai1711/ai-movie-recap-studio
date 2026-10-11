const API_BASE = '';

// Helper Functions
function showToast(msg) {
  alert(msg); // ဖုန်းပေါ်တွင် သေချာပေါက် မြင်ရစေရန် တိုက်ရိုက် Alert သုံးထားပါသည်
}

function switchView(viewId) {
  const views = ['auth-view', 'projects-view', 'studio-view', 'keys-view'];
  views.forEach(v => {
    const el = document.getElementById(v);
    if (el) el.style.display = (v === viewId) ? 'block' : 'none';
  });
  
  // Update Bottom Nav active state
  document.querySelectorAll('.nav-item').forEach(btn => {
    if (btn.getAttribute('data-view') === viewId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

// 1. Navigation Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('token');
  if (!token) {
    switchView('auth-view');
  } else {
    switchView('keys-view');
    loadKeysStatus();
  }

  // Bottom Nav Bar Clicks
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const targetView = btn.getAttribute('data-view');
      if (targetView) switchView(targetView);
    });
  });

  // Logout Button
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    localStorage.removeItem('token');
    switchView('auth-view');
    showToast('အကောင့်ထွက်ပြီးပါပြီ');
  });
});

// 2. Keys Management
async function loadKeysStatus() {
  const token = localStorage.getItem('token');
  if (!token) return;
  try {
    const res = await fetch(`${API_BASE}/api/settings/keys`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json();
      const aaiStatus = document.getElementById('assemblyai-status');
      const llmStatus = document.getElementById('llm-status');
      if (aaiStatus) aaiStatus.innerText = data.has_assemblyai_key ? '✅ Active' : 'Not Set';
      if (llmStatus) llmStatus.innerText = data.has_llm_key ? '✅ Active' : 'Not Set';
    }
  } catch (err) {
    console.error(err);
  }
}

// Save Keys Click
document.getElementById('save-keys-btn')?.addEventListener('click', async () => {
  const token = localStorage.getItem('token');
  if (!token) return showToast('အရင်ဆုံး Login ဝင်ပါ');

  const aaiKey = document.getElementById('assemblyai-key-input')?.value.trim();
  const llmKey = document.getElementById('llm-key-input')?.value.trim();

  if (!aaiKey && !llmKey) {
    return showToast('Key တစ်ခုခု ရိုက်ထည့်ပေးပါ');
  }

  try {
    const payload = {};
    if (aaiKey) payload.assemblyai_key = aaiKey;
    if (llmKey) payload.llm_key = llmKey;

    const res = await fetch(`${API_BASE}/api/settings/keys`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Key သိမ်းဆည်း၍ မရပါ');
    showToast('Key သိမ်းဆည်းပြီးပါပြီ!');
    loadKeysStatus();
  } catch (err) {
    showToast('Error: ' + err.message);
  }
});

// Test AssemblyAI Key Click
document.getElementById('test-assemblyai-btn')?.addEventListener('click', async () => {
  const token = localStorage.getItem('token');
  if (!token) return showToast('အရင်ဆုံး Login ဝင်ပါ');

  try {
    showToast('AssemblyAI နှင့် စမ်းသပ်ချိတ်ဆက်နေပါသည်...');
    const res = await fetch(`${API_BASE}/api/settings/test-assemblyai`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await res.json();
    if (res.ok && data.status === 'ok') {
      showToast('AssemblyAI ချိတ်ဆက်မှု အောင်မြင်ပါသည်!');
    } else {
      showToast('ချိတ်ဆက်မှု မအောင်မြင်ပါ: ' + (data.detail || 'Invalid Key'));
    }
  } catch (err) {
    showToast('Error: ' + err.message);
  }
});
