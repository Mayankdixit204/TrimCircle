(() => {
  let selectedStyle = null;
  let catalogByName = new Map();
  let resultUrl = null;

  const dialog = document.createElement('dialog');
  dialog.className = 'tryon-dialog';
  dialog.innerHTML = `
    <button class="tryon-close" aria-label="Close virtual try-on">×</button>
    <div class="tryon-layout">
      <section class="tryon-visual">
        <span class="kicker">Virtual try-on workspace</span>
        <h2>See it on you.</h2>
        <div class="compare" id="tryon-compare">
          <img id="tryon-before" alt="Original front photograph">
          <div class="after-wrap" id="after-wrap"><img id="tryon-after" alt="Generated hairstyle result"></div>
          <div class="empty-result">Your generated image will appear here after you import the Kaggle result.</div>
          <span class="compare-label label-before">Before</span><span class="compare-label label-after">After</span>
        </div>
        <input class="compare-range" id="compare-range" type="range" min="0" max="100" value="50" aria-label="Move before and after divider">
      </section>
      <section class="tryon-controls">
        <span class="kicker">Selected haircut</span><h3 id="tryon-style">Hairstyle</h3>
        <p class="tryon-sub">The face, expression, clothes, and background are locked in the generation instructions.</p>
        <div class="tryon-step"><div class="tryon-step-head"><b>01</b><div><h4>Choose hair colour</h4><p>Natural preserves the colour visible in your photograph.</p></div></div>
          <div class="color-options" role="group" aria-label="Hair colour">
            <button class="color-choice selected" data-color="natural" aria-label="Natural colour"><i style="background:linear-gradient(135deg,#191714,#b09070)"></i></button>
            <button class="color-choice" data-color="black" aria-label="Black"><i style="background:#151515"></i></button>
            <button class="color-choice" data-color="dark-brown" aria-label="Dark brown"><i style="background:#3a241a"></i></button>
            <button class="color-choice" data-color="warm-brown" aria-label="Warm brown"><i style="background:#76503a"></i></button>
            <button class="color-choice" data-color="blonde" aria-label="Blonde"><i style="background:#c8aa74"></i></button>
            <button class="color-choice" data-color="copper" aria-label="Copper"><i style="background:#9b4d2d"></i></button>
          </div>
        </div>
        <div class="tryon-step"><div class="tryon-step-head"><b>02</b><div><h4>Prepare private Kaggle job</h4><p>Downloads your photo and exact generation instructions as one ZIP.</p></div></div><button class="job-button" id="download-job">Download generation package</button><div class="tryon-status" id="job-status" role="status"></div></div>
        <div class="tryon-step"><div class="tryon-step-head"><b>03</b><div><h4>Import generated result</h4><p>After Kaggle creates result.png, bring it back here for comparison.</p></div></div><label class="import-label">Choose result.png<input id="import-result" type="file" accept="image/png,image/jpeg,image/webp"></label><a class="download-result" id="download-result" download="trimcircle-tryon.png">Download final image</a></div>
        <p class="tryon-warning">Facial photos are biometric data. Keep the Kaggle notebook and dataset private, then delete the files after generation.</p>
      </section>
    </div>`;
  document.body.append(dialog);

  fetch('/v1/hairstyles').then(r => r.json()).then(data => {
    catalogByName = new Map(data.items.map(item => [item.name, item]));
    enhanceCards();
  });

  function enhanceCards() {
    document.querySelectorAll('.result-card:not([data-tryon-ready])').forEach(card => {
      const name = card.querySelector('h3')?.textContent.trim();
      const style = catalogByName.get(name);
      if (!style) return;
      card.dataset.tryonReady = 'true';
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'try-button'; button.textContent = 'Preview on my face';
      button.addEventListener('click', () => openTryOn(style, card));
      card.append(button);
    });
  }

  new MutationObserver(enhanceCards).observe(document.querySelector('#recommendations'), {childList:true});

  function openTryOn(style, card) {
    selectedStyle = style;
    document.querySelectorAll('.result-card').forEach(item => item.classList.remove('selected-tryon'));
    card.classList.add('selected-tryon');
    document.querySelector('#tryon-style').textContent = style.name;
    document.querySelector('#tryon-before').src = document.querySelector('.capture[data-view="front"] img').src;
    dialog.showModal();
  }

  dialog.querySelector('.tryon-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  dialog.querySelectorAll('.color-choice').forEach(button => button.addEventListener('click', () => {
    dialog.querySelectorAll('.color-choice').forEach(item => item.classList.remove('selected'));
    button.classList.add('selected');
  }));
  document.querySelector('#compare-range').addEventListener('input', event => {
    document.querySelector('#after-wrap').style.width = `${event.target.value}%`;
  });

  document.querySelector('#download-job').addEventListener('click', async event => {
    const button = event.currentTarget;
    const status = document.querySelector('#job-status');
    button.disabled = true; button.textContent = 'Preparing package…'; status.textContent = '';
    try {
      const sourceResponse = await fetch(document.querySelector('#tryon-before').src);
      const sourceBlob = await sourceResponse.blob();
      const form = new FormData();
      form.append('front', sourceBlob, 'front-photo.png');
      form.append('style_id', selectedStyle.id);
      form.append('color', dialog.querySelector('.color-choice.selected').dataset.color);
      form.append('texture', document.querySelector('[data-name="texture"] .selected')?.dataset.value || 'natural');
      const response = await fetch('/v1/tryon/prepare', {method:'POST', body:form});
      if (!response.ok) throw new Error('Could not prepare the package. Check the front photo and retry.');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a'); link.href = url;
      const disposition = response.headers.get('Content-Disposition') || '';
      link.download = disposition.split('filename=')[1]?.replaceAll('"','') || 'trimcircle-tryon-job.zip';
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = 'Package ready. Upload it only to your private Kaggle workflow.';
    } catch (error) { status.textContent = error.message; }
    finally { button.disabled = false; button.textContent = 'Download generation package'; }
  });

  document.querySelector('#import-result').addEventListener('change', event => {
    const file = event.target.files[0]; if (!file) return;
    if (resultUrl) URL.revokeObjectURL(resultUrl);
    resultUrl = URL.createObjectURL(file);
    document.querySelector('#tryon-after').src = resultUrl;
    document.querySelector('#tryon-compare').classList.add('ready');
    const download = document.querySelector('#download-result');
    download.href = resultUrl; download.style.display = 'flex';
  });
})();
