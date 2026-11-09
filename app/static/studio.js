const files = {};
const selections = {};
let analysis = { face_shape: 'unknown', alternative_face_shape: null, uncertainty: 'unknown', metrics: {} };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const safe = (value) => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

function showStage(number) {
  $$('.stage').forEach(stage => stage.classList.toggle('active', stage.dataset.stage === String(number)));
  $$('.steps li').forEach((step, index) => {
    step.classList.toggle('active', index + 1 === number);
    step.classList.toggle('done', index + 1 < number);
  });
  $('#studio').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
}

const captureViews = {
  front: {label: 'Front view', title: 'Look straight ahead', instruction: 'Keep your face inside the oval, at eye level, with a neutral expression.'},
  left: {label: 'Left profile', title: 'Turn to your left', instruction: 'Keep your shoulders still and turn your head until your left profile is visible.'},
  right: {label: 'Right profile', title: 'Turn to your right', instruction: 'Keep your shoulders still and turn your head until your right profile is visible.'}
};
const captureOrder = Object.keys(captureViews);
const camera = $('#camera');
const cameraCanvas = $('#camera-canvas');
const cameraShell = $('#camera-shell');
const cameraFeedback = $('#camera-feedback');
const startCameraButton = $('#start-camera');
const captureButton = $('#capture-photo');
const stopCameraButton = $('#stop-camera');
let activeView = 'front';
let cameraStream = null;
let checkTimer = null;
let checkPending = false;
let captureReady = false;

function updateCaptureCopy() {
  const view = captureViews[activeView];
  const position = captureOrder.indexOf(activeView) + 1;
  $('#capture-step').textContent = `${view.label} · ${position} of 3`;
  $('#capture-title').textContent = view.title;
  $('#capture-instruction').textContent = view.instruction;
  captureButton.textContent = `Capture ${view.label.toLowerCase()}`;
  captureButton.disabled = !captureReady || !cameraStream;
}

function setCaptureReady(ready, message) {
  captureReady = ready;
  cameraShell.classList.toggle('ready', ready);
  cameraFeedback.textContent = message;
  captureButton.disabled = !ready || !cameraStream;
}

function drawCameraFrame(maximumWidth = 720) {
  const sourceWidth = camera.videoWidth;
  const sourceHeight = camera.videoHeight;
  if (!sourceWidth || !sourceHeight) return false;
  const scale = Math.min(1, maximumWidth / sourceWidth);
  cameraCanvas.width = Math.round(sourceWidth * scale);
  cameraCanvas.height = Math.round(sourceHeight * scale);
  const context = cameraCanvas.getContext('2d', {alpha: false});
  context.save();
  context.translate(cameraCanvas.width, 0);
  context.scale(-1, 1);
  context.drawImage(camera, 0, 0, cameraCanvas.width, cameraCanvas.height);
  context.restore();
  return true;
}

function canvasBlob(quality = .9) {
  return new Promise(resolve => cameraCanvas.toBlob(resolve, 'image/jpeg', quality));
}

async function checkLiveFrame() {
  if (!cameraStream || checkPending || !drawCameraFrame(640)) return;
  checkPending = true;
  try {
    const blob = await canvasBlob(.78);
    if (!blob) throw new Error('Could not read the camera frame.');
    const body = new FormData();
    body.append('photo', blob, 'camera-frame.jpg');
    body.append('view', activeView);
    const response = await fetch('/v1/capture-check', {method: 'POST', body});
    if (!response.ok) throw new Error('Live face check is unavailable.');
    const result = await response.json();
    setCaptureReady(result.ready, result.message);
  } catch (error) {
    setCaptureReady(false, error.message);
  } finally {
    checkPending = false;
  }
}

async function startCamera() {
  if (!navigator.mediaDevices?.getUserMedia) {
    setCaptureReady(false, 'This browser cannot access a camera. Use a current browser over HTTPS or localhost.');
    return;
  }
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {facingMode: 'user', width: {ideal: 1280}, height: {ideal: 960}}
    });
    camera.srcObject = cameraStream;
    await camera.play();
    cameraShell.classList.add('live');
    startCameraButton.hidden = true;
    captureButton.hidden = false;
    stopCameraButton.hidden = false;
    setCaptureReady(false, 'Checking face position…');
    clearInterval(checkTimer);
    checkTimer = setInterval(checkLiveFrame, 1100);
    await checkLiveFrame();
  } catch (error) {
    setCaptureReady(false, error.name === 'NotAllowedError'
      ? 'Camera permission was blocked. Allow camera access in your browser settings and try again.'
      : 'The camera could not start. Close other camera apps and try again.');
  }
}

function stopCamera() {
  clearInterval(checkTimer);
  checkTimer = null;
  cameraStream?.getTracks().forEach(track => track.stop());
  cameraStream = null;
  camera.srcObject = null;
  cameraShell.classList.remove('live', 'ready');
  startCameraButton.hidden = false;
  captureButton.hidden = true;
  stopCameraButton.hidden = true;
  setCaptureReady(false, 'Camera stopped. Start it to capture or retake a view.');
}

async function captureCurrentView() {
  if (!captureReady || !drawCameraFrame(960)) return;
  const blob = await canvasBlob(.92);
  if (!blob) return;
  const file = new File([blob], `${activeView}.jpg`, {type: 'image/jpeg'});
  files[activeView] = file;
  const thumb = $(`.capture-thumb[data-view="${activeView}"]`);
  const image = $('img', thumb);
  if (image.dataset.url) URL.revokeObjectURL(image.dataset.url);
  image.dataset.url = URL.createObjectURL(blob);
  image.src = image.dataset.url;
  thumb.classList.add('done');
  $('button', thumb).disabled = false;

  const nextView = captureOrder.find(view => !files[view]);
  $('#analyze').disabled = Boolean(nextView);
  if (nextView) {
    activeView = nextView;
    setCaptureReady(false, `Next: ${captureViews[nextView].label}. Adjust your position.`);
    updateCaptureCopy();
    await checkLiveFrame();
  } else {
    stopCamera();
    cameraFeedback.textContent = 'All three views captured. You can analyze or retake any view.';
  }
}

startCameraButton.addEventListener('click', startCamera);
captureButton.addEventListener('click', captureCurrentView);
stopCameraButton.addEventListener('click', stopCamera);
$$('.capture-thumb').forEach(thumb => $('button', thumb).addEventListener('click', async () => {
  activeView = thumb.dataset.view;
  delete files[activeView];
  thumb.classList.remove('done');
  $('button', thumb).disabled = true;
  $('#analyze').disabled = true;
  setCaptureReady(false, `Retake ${captureViews[activeView].label.toLowerCase()}.`);
  updateCaptureCopy();
  if (!cameraStream) await startCamera();
}));
updateCaptureCopy();

$('#analyze').addEventListener('click', async () => {
  if (cameraStream) stopCamera();
  const button = $('#analyze');
  const status = $('#analysis-status');
  const payload = new FormData();
  Object.entries(files).forEach(([view, file]) => payload.append(view, file));
  button.disabled = true;
  button.innerHTML = 'Mapping 468 landmarks…';
  status.innerHTML = '<div class="analysis-progress"><b>Analyzing facial geometry</b><span>Checking image quality, pose, and proportions one view at a time.</span></div>';
  try {
    const response = await fetch('/v1/analyze-face', {method:'POST', body:payload});
    if (!response.ok) throw new Error('Analysis service returned an error.');
    analysis = await response.json();
    const badPhotos = (analysis.photo_checks || []).filter(item => !item.valid);
    if (badPhotos.length) {
      status.innerHTML = `<div class="error"><b>Retake needed:</b> ${badPhotos.map(item => `${safe(item.view)} — ${safe(item.messages.join(' '))}`).join(' ')}</div>`;
      return;
    }
    $('#face_shape').value = analysis.face_shape;
    const metrics = analysis.metrics || {};
    const alternative = analysis.alternative_face_shape ? `; possible alternative: ${safe(analysis.alternative_face_shape)}` : '';
    $('#face-report').innerHTML = `<div class="shape-badge"><small>Geometry estimate</small><strong>${safe(analysis.face_shape)}</strong><small>Uncertainty: ${safe(analysis.uncertainty)}${alternative}</small></div><div class="metrics"><div class="metric"><b>${safe(metrics.length_to_width || '—')}</b><small>Length / width</small></div><div class="metric"><b>${safe(metrics.forehead_to_cheek || '—')}</b><small>Forehead / cheek</small></div><div class="metric"><b>${safe(metrics.jaw_to_cheek || '—')}</b><small>Jaw / cheek</small></div></div>`;
    showStage(2);
  } catch (error) {
    status.innerHTML = `<div class="error"><b>Couldn’t analyze these photos.</b> ${safe(error.message)} You can retry without losing your selections.</div>`;
  } finally {
    button.disabled = false;
    button.innerHTML = 'Analyze my face <span>→</span>';
  }
});

$$('.segmented').forEach(group => {
  $$('button', group).forEach(button => button.addEventListener('click', () => {
    $$('button', group).forEach(item => item.classList.remove('selected'));
    button.classList.add('selected');
    selections[group.dataset.name] = button.dataset.value;
  }));
});

$('#profile-form').addEventListener('submit', async event => {
  event.preventDefault();
  const required = ['texture','density','current_length','desired_length','maintenance'];
  const missing = required.filter(key => !selections[key]);
  if (missing.length) {
    $('#profile-error').textContent = `Please choose: ${missing.map(item => item.replace('_',' ')).join(', ')}.`;
    return;
  }
  $('#profile-error').textContent = '';
  const submit = $('#profile-form [type="submit"]');
  submit.disabled = true;
  submit.textContent = 'Ranking your matches…';
  const profile = {...selections, face_shape: $('#face_shape').value, excluded_styles: [], limit: 5};
  try {
    const response = await fetch('/v1/recommendations', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(profile)});
    if (!response.ok) throw new Error('Ranking failed. Please review the profile.');
    const data = await response.json();
    $('#results-note').textContent = data.notice;
    $('#result-summary').innerHTML = `<div><span>Face shape</span><b>${safe(profile.face_shape)}</b></div><div><span>Texture</span><b>${safe(profile.texture)}</b></div><div><span>Desired length</span><b>${safe(profile.desired_length)}</b></div><div><span>Effort</span><b>${safe(profile.maintenance)}</b></div>`;
    $('#recommendations').innerHTML = data.recommendations.length ? data.recommendations.map((item,index) => `<article class="result-card"><span class="rank">Option ${String(index+1).padStart(2,'0')}</span><span class="score" aria-label="${item.score} internal ranking points">${item.score}<small> pts</small></span><h3>${safe(item.name)}</h3><p>${safe(item.description)}</p><ul class="why">${item.reasons.map(reason => `<li>${safe(reason)}</li>`).join('')}</ul><span class="tag">${safe(item.maintenance)} maintenance</span></article>`).join('') : '<div class="analysis-progress"><b>No exact match yet</b><span>Go back and try a different desired length.</span></div>';
    showStage(3);
  } catch (error) { $('#profile-error').textContent = error.message; }
  finally { submit.disabled = false; submit.innerHTML = 'Build my shortlist <span>→</span>'; }
});

$$('.back').forEach(button => button.addEventListener('click', () => showStage(1)));
$$('.profile-back').forEach(button => button.addEventListener('click', () => showStage(2)));
$('.restart').addEventListener('click', () => location.reload());
const guide = $('#guide');
$('#demo-help').addEventListener('click', () => guide.showModal());
$('.dialog-close').addEventListener('click', () => guide.close());
guide.addEventListener('click', event => { if (event.target === guide) guide.close(); });
