(() => {
  let currentJob = null;
  let pollTimer = null;
  let styles = new Map();
  fetch('/v1/hairstyles').then(response => response.json()).then(data => {
    styles = new Map(data.items.map(item => [item.name, item]));
  });

  const mount = () => {
    const manualButton = document.querySelector('#download-job');
    if (!manualButton || document.querySelector('#create-job')) return;
    manualButton.classList.add('manual');
    manualButton.textContent = 'Download manual Kaggle package';
    manualButton.insertAdjacentHTML('beforebegin', `
      <button class="queue-button" id="create-job" type="button">Create secure generation job</button>
      <div class="queue-card" id="queue-card" aria-live="polite">
        <div class="queue-line"><span class="queue-state" id="queue-state">Preparing</span><button class="delete-job" id="delete-job" type="button">Delete job</button></div>
        <span class="queue-id" id="queue-id"></span>
        <div class="progress-track" role="progressbar" aria-label="Generation progress"><div class="progress-fill" id="progress-fill"></div></div>
        <p class="queue-hint" id="queue-hint">The page can stay open while the GPU worker processes this request.</p>
      </div>`);
    document.querySelector('#create-job').addEventListener('click', createJob);
    document.querySelector('#delete-job').addEventListener('click', deleteJob);
    document.querySelector('#import-result').addEventListener('change', uploadImportedResult);
  };

  async function sourceBlob() {
    const source = document.querySelector('#tryon-before').src;
    if (!source) throw new Error('Front photograph is unavailable.');
    return (await fetch(source)).blob();
  }

  async function createJob(event) {
    const button = event.currentTarget;
    const style = styles.get(document.querySelector('#tryon-style').textContent.trim());
    if (!style) return;
    button.disabled = true; button.textContent = 'Uploading optimized photo…';
    try {
      const form = new FormData();
      form.append('front', await sourceBlob(), 'front-photo.png');
      form.append('style_id', style.id);
      form.append('color', document.querySelector('.color-choice.selected')?.dataset.color || 'natural');
      form.append('texture', document.querySelector('[data-name="texture"] .selected')?.dataset.value || 'natural');
      const response = await fetch('/v1/tryon/jobs', {method:'POST', body:form});
      if (!response.ok) throw new Error('The job could not be created. Check the front photo.');
      currentJob = await response.json();
      renderJob(currentJob);
      startPolling();
    } catch (error) {
      document.querySelector('#job-status').textContent = error.message;
    } finally {
      button.disabled = false; button.textContent = 'Create secure generation job';
    }
  }

  function renderJob(job) {
    document.querySelector('#queue-card').classList.add('visible');
    document.querySelector('#queue-state').textContent = job.status.replaceAll('_',' ');
    document.querySelector('#queue-id').textContent = `Job ${job.id} · automatically deleted ${new Date(job.expires_at).toLocaleString()}`;
    document.querySelector('#progress-fill').style.width = `${job.progress}%`;
    const hints = {
      awaiting_gpu:'Waiting for a configured Kaggle/cloud GPU worker. Use the manual package while developing.',
      queued:'Your request is next in the generation queue.',
      generating:'The GPU is changing only the hairstyle.',
      completed:'Generation complete. Your result is ready.',
      failed:job.error || 'Generation failed. You can retry safely.'
    };
    document.querySelector('#queue-hint').textContent = hints[job.status] || 'Processing request.';
    if (job.result_ready) loadRemoteResult(job.id);
  }

  function startPolling() {
    clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      if (!currentJob) return;
      const response = await fetch(`/v1/tryon/jobs/${currentJob.id}`);
      if (response.status === 404) { clearInterval(pollTimer); currentJob = null; return; }
      currentJob = await response.json(); renderJob(currentJob);
      if (['completed','failed'].includes(currentJob.status)) clearInterval(pollTimer);
    }, 5000);
  }

  async function uploadImportedResult(event) {
    const file = event.target.files[0];
    if (!file || !currentJob) return;
    const form = new FormData(); form.append('result', file, file.name);
    const response = await fetch(`/v1/tryon/jobs/${currentJob.id}/result`, {method:'POST', body:form});
    if (!response.ok) { document.querySelector('#job-status').textContent = 'Result could not be attached to this job.'; return; }
    currentJob = await response.json(); renderJob(currentJob);
  }

  async function loadRemoteResult(jobId) {
    const image = document.querySelector('#tryon-after');
    const url = `/v1/tryon/jobs/${jobId}/result`;
    if (image.src.endsWith(url)) return;
    image.src = url;
    document.querySelector('#tryon-compare').classList.add('ready');
    const download = document.querySelector('#download-result');
    download.href = url; download.style.display = 'flex';
  }

  async function deleteJob() {
    if (!currentJob) return;
    await fetch(`/v1/tryon/jobs/${currentJob.id}`, {method:'DELETE'});
    clearInterval(pollTimer); currentJob = null;
    document.querySelector('#queue-card').classList.remove('visible');
    document.querySelector('#job-status').textContent = 'Private job and stored images deleted.';
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
