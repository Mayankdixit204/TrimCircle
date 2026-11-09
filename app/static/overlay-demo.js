(() => {
  if (!new URLSearchParams(location.search).has('demo2d')) return;
  window.addEventListener('load', () => {
    for (const view of ['front', 'left', 'right']) {
      const image = document.querySelector(`.capture[data-view="${view}"] img`);
      image.src = `/static/hairstyles/textured-crop/${view}.webp`;
      image.closest('.capture').classList.add('has-image');
    }
    document.querySelectorAll('.stage').forEach(stage => stage.classList.remove('active'));
    document.querySelector("[data-stage='3']").classList.add('active');
    document.querySelector('#recommendations').innerHTML = '<article class="result-card"><span class="rank">Interactive demo</span><h3>Textured Crop</h3><p>Test the three-view 2D placement editor without uploading personal photographs.</p></article>';
    setTimeout(() => document.querySelector('.try-button')?.click(), 800);
  });
})();
