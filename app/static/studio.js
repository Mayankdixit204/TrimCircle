const files = {};
const selections = {};
let analysis = { face_shape: 'unknown', confidence: 0, metrics: {} };
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

$$('.capture').forEach(card => {
  const input = $('input', card);
  input.addEventListener('change', () => {
    if (!input.files[0]) return;
    const view = card.dataset.view;
    files[view] = input.files[0];
    const image = $('img', card);
    if (image.dataset.url) URL.revokeObjectURL(image.dataset.url);
    image.dataset.url = URL.createObjectURL(input.files[0]);
    image.src = image.dataset.url;
    card.classList.add('has-image');
    $('#analyze').disabled = !['front','left','right'].every(key => files[key]);
  });
});

$('#analyze').addEventListener('click', async () => {
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
    $('#face-report').innerHTML = `<div class="shape-badge"><small>Geometry estimate</small><strong>${safe(analysis.face_shape)}</strong><small>${Math.round(analysis.confidence * 100)}% heuristic confidence</small></div><div class="metrics"><div class="metric"><b>${safe(metrics.length_to_width || '—')}</b><small>Length / width</small></div><div class="metric"><b>${safe(metrics.forehead_to_cheek || '—')}</b><small>Forehead / cheek</small></div><div class="metric"><b>${safe(metrics.jaw_to_cheek || '—')}</b><small>Jaw / cheek</small></div></div>`;
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
  const profile = {...selections, face_shape: $('#face_shape').value, excluded_styles: [], limit: 6};
  try {
    const response = await fetch('/v1/recommendations', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(profile)});
    if (!response.ok) throw new Error('Ranking failed. Please review the profile.');
    const data = await response.json();
    $('#results-note').textContent = data.notice;
    $('#result-summary').innerHTML = `<div><span>Face shape</span><b>${safe(profile.face_shape)}</b></div><div><span>Texture</span><b>${safe(profile.texture)}</b></div><div><span>Desired length</span><b>${safe(profile.desired_length)}</b></div><div><span>Effort</span><b>${safe(profile.maintenance)}</b></div>`;
    $('#recommendations').innerHTML = data.recommendations.length ? data.recommendations.map((item,index) => `<article class="result-card"><span class="rank">Match ${String(index+1).padStart(2,'0')}</span><span class="score" aria-label="${item.score} percent match">${item.score}</span><h3>${safe(item.name)}</h3><p>${safe(item.description)}</p><ul class="why">${item.reasons.map(reason => `<li>${safe(reason)}</li>`).join('')}</ul><span class="tag">${safe(item.maintenance)} maintenance</span></article>`).join('') : '<div class="analysis-progress"><b>No exact match yet</b><span>Go back and try a different desired length.</span></div>';
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
