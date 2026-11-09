const form = document.querySelector('#recommendation-form');
const validateButton = document.querySelector('#validate-photos');
const photoStatus = document.querySelector('#photo-status');
const formError = document.querySelector('#form-error');
const results = document.querySelector('#results');
const resultList = document.querySelector('#result-list');
const resultsNotice = document.querySelector('#results-notice');

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
})[character]);

validateButton.addEventListener('click', async () => {
  const data = new FormData();
  for (const view of ['front', 'left', 'right']) {
    const file = form.elements[view].files[0];
    if (!file) {
      photoStatus.innerHTML = '<p class="fail">Please choose all three photos first.</p>';
      form.elements[view].focus();
      return;
    }
    data.append(view, file);
  }

  validateButton.disabled = true;
  validateButton.textContent = 'Checking photos…';
  photoStatus.textContent = 'Checking each image one at a time.';
  try {
    const response = await fetch('/v1/validate-photos', { method: 'POST', body: data });
    if (!response.ok) throw new Error('Photo check failed.');
    const checks = await response.json();
    photoStatus.innerHTML = `<ul>${checks.map((check) =>
      `<li class="${check.valid ? 'pass' : 'fail'}"><strong>${escapeHtml(check.view)}</strong>: ${check.messages.map(escapeHtml).join(' ')}</li>`
    ).join('')}</ul>`;
  } catch (error) {
    photoStatus.innerHTML = `<p class="fail">${escapeHtml(error.message)} Please try again.</p>`;
  } finally {
    validateButton.disabled = false;
    validateButton.textContent = 'Check photo quality';
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  formError.hidden = true;
  if (!form.reportValidity()) return;

  const submitButton = form.querySelector('[type="submit"]');
  const payload = {
    face_shape: form.elements.face_shape.value,
    texture: form.elements.texture.value,
    density: form.elements.density.value,
    current_length: form.elements.current_length.value,
    desired_length: form.elements.desired_length.value,
    maintenance: form.elements.maintenance.value,
    excluded_styles: form.elements.excluded_styles.value.split(',').map((item) => item.trim()).filter(Boolean),
    limit: 5
  };

  submitButton.disabled = true;
  submitButton.textContent = 'Ranking styles…';
  try {
    const response = await fetch('/v1/recommendations', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error('We could not create recommendations from this profile.');
    const data = await response.json();
    resultsNotice.textContent = data.notice;
    resultList.innerHTML = data.recommendations.length ? data.recommendations.map((item) => `
      <article class="result-card">
        <div class="score" aria-label="Compatibility score ${item.score} out of 100">${item.score}</div>
        <h3>${escapeHtml(item.name)}</h3>
        <p>${escapeHtml(item.description)}</p>
        <ul>${item.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join('')}</ul>
        <div class="meta">${escapeHtml(item.maintenance)} maintenance · ${item.suitable_textures.map(escapeHtml).join(', ')}</div>
      </article>`).join('') : '<p>No styles match all selected constraints. Try another desired length.</p>';
    results.hidden = false;
    results.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    document.querySelector('#results-title').focus();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = 'Show my recommendations';
  }
});

