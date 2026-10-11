// Drawer Toggle
const drawer = document.getElementById('sidebar-drawer');
const backdrop = document.getElementById('backdrop');

document.getElementById('menu-toggle-btn')?.addEventListener('click', () => {
  drawer.classList.add('open');
  backdrop.classList.add('open');
});

const closeDrawer = () => {
  drawer.classList.remove('open');
  backdrop.classList.remove('open');
};

document.getElementById('close-drawer-btn')?.addEventListener('click', closeDrawer);
backdrop?.addEventListener('click', closeDrawer);

// View Switcher (Studio vs Settings)
document.querySelectorAll('.drawer-menu .menu-item').forEach(item => {
  item.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelectorAll('.drawer-menu .menu-item').forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    
    const target = item.getAttribute('data-view');
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(target)?.classList.add('active');
    closeDrawer();
  });
});

// Studio Tab Switching (Video, Voice, Captions, Extras, Gemini)
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    
    btn.classList.add('active');
    const tabId = btn.getAttribute('data-tab');
    document.getElementById(tabId)?.classList.add('active');
  });
});

// Interactive Sliders Update
document.getElementById('zoom-slider')?.addEventListener('input', (e) => {
  document.getElementById('zoom-val').innerText = `${e.target.value}%`;
});

document.getElementById('speed-slider')?.addEventListener('input', (e) => {
  const v = e.target.value;
  document.getElementById('speed-val').innerText = `${v >= 0 ? '+' : ''}${v}%`;
});

document.getElementById('pitch-slider')?.addEventListener('input', (e) => {
  const v = e.target.value;
  document.getElementById('pitch-val').innerText = `${v >= 0 ? '+' : ''}${v}Hz`;
});

document.getElementById('font-size-slider')?.addEventListener('input', (e) => {
  const sz = e.target.value;
  document.getElementById('font-size-val').innerText = `${sz}px`;
  document.getElementById('caption-preview-text').style.fontSize = `${sz}px`;
});

document.getElementById('pos-slider')?.addEventListener('input', (e) => {
  document.getElementById('pos-val').innerText = `${e.target.value}%`;
});

// Color Swatches
document.querySelectorAll('.color-swatch').forEach(swatch => {
  swatch.addEventListener('click', () => {
    document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('active'));
    swatch.classList.add('active');
    const color = swatch.getAttribute('data-color');
    document.getElementById('caption-preview-text').style.color = color;
  });
});

// Radio & Choice Button Groups
document.querySelectorAll('.btn-group .btn-choice').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.parentElement.querySelectorAll('.btn-choice').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});

// ==========================================
// CLIENT-SIDE (IN-DEVICE) RENDER ENGINE
// ==========================================
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
  
  if (!videoFile) {
    return alert('ကျေးဇူးပြု၍ "Choose video file" ကို နှိပ်ပြီး ဖုန်းထဲမှ မူရင်းဗီဒီယိုကို အရင်ရွေးပါ');
  }

  const pCard = document.getElementById('render-progress-card');
  const sText = document.getElementById('render-status-text');
  const pText = document.getElementById('render-percent');
  const pBar = document.getElementById('render-progress-bar');
  const dBox = document.getElementById('download-result-box');
  const dLink = document.getElementById('download-final-video');

  try {
    pCard.style.display = 'block';
    dBox.style.display = 'none';
    sText.innerText = 'FFmpeg Engine အား ဖုန်းထဲသို့ ထည့်သွင်းနေပါသည်...';
    pBar.style.width = '10%';
    pText.innerText = '10%';

    const ffmpeg = await loadFFmpeg();

    ffmpeg.setProgress(({ ratio }) => {
      const p = Math.max(0, Math.min(100, Math.round(ratio * 100)));
      pBar.style.width = `${p}%`;
      pText.innerText = `${p}%`;
    });

    sText.innerText = 'ဗီဒီယိုဖိုင်အား ဖတ်ယူနေပါသည်...';
    const { fetchFile } = FFmpeg;
    ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(videoFile));

    sText.innerText = 'ဖုန်းပေါ်တွင် ဗီဒီယို ဖြတ်ညှပ်ကပ် စတင်ထုတ်ယူနေပါသည်...';
    
    // Fast stream copy (Server RAM မသုံးဘဲ ဖုန်းထဲတွင် စက္ကန့်ပိုင်းအတွင်း ပြီးစီးပါသည်)
    await ffmpeg.run('-i', 'input.mp4', '-c', 'copy', 'output.mp4');

    sText.innerText = 'ဗီဒီယို အောင်မြင်စွာ ထွက်ရှိပါပြီ!';
    pBar.style.width = '100%';
    pText.innerText = '100%';

    const data = ffmpeg.FS('readFile', 'output.mp4');
    const blob = new Blob([data.buffer], { type: 'video/mp4' });
    dLink.href = URL.createObjectURL(blob);
    dLink.download = `Recap_${Date.now()}.mp4`;
    dBox.style.display = 'block';

    ffmpeg.FS('unlink', 'input.mp4');
    ffmpeg.FS('unlink', 'output.mp4');

  } catch (err) {
    alert('Render Error: ' + err.message);
    sText.innerText = 'အမှားဖြစ်သွားပါသည်: ' + err.message;
  }
});

