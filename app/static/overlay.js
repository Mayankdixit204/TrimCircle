(() => {
  const VIEWS = ['front','left','right'];
  const states = Object.fromEntries(VIEWS.map(view => [view,{x:0,y:0,scale:1,rotation:0,opacity:1,color:'natural'}]));
  const photos = {};
  const hairs = {};
  const anchors = {};
  let activeView = 'front';
  let selectedStyle = null;
  let metadata = null;
  let dragging = false;
  let pointer = {x:0,y:0};

  const dialog = document.createElement('dialog');
  dialog.className = 'overlay-dialog';
  dialog.innerHTML = `<button class="overlay-close" aria-label="Close 2D try-on">×</button><div class="overlay-layout">
    <section class="overlay-stage"><div class="overlay-heading"><div><span class="kicker">Three-view 2D try-on</span><h2>Fit the cut to your face.</h2><p>Automatic landmark placement with touch-friendly fine tuning.</p></div><div class="view-tabs" role="tablist">${VIEWS.map((view,i)=>`<button class="view-tab ${i===0?'selected':''}" data-view="${view}" role="tab">${view}</button>`).join('')}</div></div>
      <div class="canvas-wrap"><canvas id="overlay-canvas" aria-label="Hairstyle preview editor"></canvas><div class="canvas-status" id="canvas-status">Front view</div><div class="overlay-loading" id="overlay-loading"><div><b>Mapping hairstyle</b><span>Reading face position and preparing three views…</span></div></div></div><p class="drag-tip">Drag the hairstyle directly. Use sliders or arrow buttons for precise adjustments.</p>
    </section>
    <aside class="overlay-controls"><span class="kicker">Selected style</span><h3 id="overlay-style">Textured Crop</h3><p class="overlay-note">Changes are stored separately for each camera angle.</p><div id="asset-warning"></div>
      <div class="control-group"><div class="control-head"><label for="overlay-scale">Size</label><span class="control-value" id="scale-value">100%</span></div><input id="overlay-scale" type="range" min="55" max="190" value="100"></div>
      <div class="control-group"><div class="control-head"><label for="overlay-rotation">Rotation</label><span class="control-value" id="rotation-value">0°</span></div><input id="overlay-rotation" type="range" min="-30" max="30" value="0"></div>
      <div class="control-group"><div class="control-head"><label for="overlay-opacity">Blend</label><span class="control-value" id="opacity-value">100%</span></div><input id="overlay-opacity" type="range" min="35" max="100" value="100"></div>
      <div class="control-group"><div class="control-head"><label>Position</label><span class="control-value">2 px steps</span></div><div class="nudge-grid"><button data-dx="0" data-dy="-2" aria-label="Move up">↑</button><button data-dx="-2" data-dy="0" aria-label="Move left">←</button><button data-reset-position aria-label="Reset position">•</button><button data-dx="2" data-dy="0" aria-label="Move right">→</button></div></div>
      <div class="control-group"><div class="control-head"><label>Hair colour</label></div><div class="overlay-colors"><button class="overlay-color selected" data-color="natural" style="background:linear-gradient(135deg,#201711,#80614d)" aria-label="Natural"></button><button class="overlay-color" data-color="#151311" style="background:#151311" aria-label="Black"></button><button class="overlay-color" data-color="#4a2e20" style="background:#4a2e20" aria-label="Dark brown"></button><button class="overlay-color" data-color="#885237" style="background:#885237" aria-label="Warm brown"></button><button class="overlay-color" data-color="#bd9559" style="background:#bd9559" aria-label="Blonde"></button><button class="overlay-color" data-color="#a74e2c" style="background:#a74e2c" aria-label="Copper"></button></div></div>
      <div class="overlay-actions"><button data-reset>Reset this view</button><button class="save-view" data-download>Download current view</button><button data-download-all>Download all three views</button></div>
    </aside></div>`;
  document.body.append(dialog);
  const canvas = dialog.querySelector('#overlay-canvas');
  const context = canvas.getContext('2d');

  function imageFrom(url){return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=reject;image.src=url;});}
  async function blobFromPreview(view){const src=document.querySelector(`.capture[data-view="${view}"] img`)?.src;if(!src)throw new Error(`Missing ${view} photo`);return (await fetch(src)).blob();}

  async function openEditor(style){
    selectedStyle=style; dialog.querySelector('#overlay-style').textContent=style.name; dialog.showModal();
    dialog.querySelector('#overlay-loading').hidden=false;
    const supported=style.id==='textured-crop';
    dialog.querySelector('#asset-warning').innerHTML=supported?'':`<div class="asset-warning"><strong>Demo overlay:</strong> ${style.name} does not have three prepared assets yet, so the Textured Crop asset is shown for placement testing.</div>`;
    try{
      metadata=await fetch('/static/hairstyles/textured-crop/metadata.json',{cache:'no-store'}).then(r=>r.json());
      const form=new FormData();
      for(const view of VIEWS){const blob=await blobFromPreview(view);form.append(view,blob,`${view}.png`);photos[view]=await imageFrom(URL.createObjectURL(blob));}
      const response=await fetch('/v1/overlay/anchors',{method:'POST',body:form});
      if(!response.ok)throw new Error('Automatic placement could not be calculated.');
      const data=await response.json();data.anchors.forEach(anchor=>anchors[anchor.view]=anchor);
      await Promise.all(VIEWS.map(async view=>{hairs[view]=await imageFrom(`/static/hairstyles/textured-crop/${metadata.views[view].asset}`);resetView(view);}));
      setView('front');
    }catch(error){dialog.querySelector('#asset-warning').innerHTML=`<div class="asset-warning">${error.message} Close the editor and confirm all three photos are loaded.</div>`;}
    finally{dialog.querySelector('#overlay-loading').hidden=true;}
  }

  function resetView(view){
    const anchor=anchors[view]||{center_x:.5,hairline_y:.24,face_width:.46,rotation:0};
    states[view]={x:anchor.center_x,y:anchor.hairline_y,scale:1,rotation:anchor.rotation,opacity:1,color:'natural'};
  }

  function setView(view){activeView=view;dialog.querySelectorAll('.view-tab').forEach(tab=>tab.classList.toggle('selected',tab.dataset.view===view));syncControls();render();}
  function syncControls(){const s=states[activeView];dialog.querySelector('#overlay-scale').value=Math.round(s.scale*100);dialog.querySelector('#overlay-rotation').value=s.rotation;dialog.querySelector('#overlay-opacity').value=Math.round(s.opacity*100);dialog.querySelector('#scale-value').textContent=`${Math.round(s.scale*100)}%`;dialog.querySelector('#rotation-value').textContent=`${Math.round(s.rotation)}°`;dialog.querySelector('#opacity-value').textContent=`${Math.round(s.opacity*100)}%`;dialog.querySelectorAll('.overlay-color').forEach(b=>b.classList.toggle('selected',b.dataset.color===s.color));dialog.querySelector('#canvas-status').textContent=`${activeView[0].toUpperCase()+activeView.slice(1)} view · ${anchors[activeView]?.detected?'landmarks detected':'manual fallback'}`;}

  function render(){
    const photo=photos[activeView],hair=hairs[activeView],anchor=anchors[activeView];if(!photo||!hair||!anchor)return;
    const max=1280,ratio=Math.min(1,max/Math.max(photo.naturalWidth,photo.naturalHeight));canvas.width=Math.round(photo.naturalWidth*ratio);canvas.height=Math.round(photo.naturalHeight*ratio);context.clearRect(0,0,canvas.width,canvas.height);context.drawImage(photo,0,0,canvas.width,canvas.height);
    const s=states[activeView],viewMeta=metadata.views[activeView];const drawWidth=anchor.face_width*canvas.width*viewMeta.width_ratio*s.scale;const drawHeight=drawWidth*(hair.naturalHeight/hair.naturalWidth);const cx=s.x*canvas.width, hairline=s.y*canvas.height;const cy=hairline+drawHeight*(.5-viewMeta.hairline_offset);
    context.save();context.translate(cx,cy);context.rotate(s.rotation*Math.PI/180);context.globalAlpha=s.opacity;context.drawImage(hair,-drawWidth/2,-drawHeight/2,drawWidth,drawHeight);
    if(s.color!=='natural'){context.globalCompositeOperation='source-atop';context.globalAlpha=.48*s.opacity;context.fillStyle=s.color;context.fillRect(-drawWidth/2,-drawHeight/2,drawWidth,drawHeight);context.globalCompositeOperation='multiply';context.globalAlpha=.22*s.opacity;context.drawImage(hair,-drawWidth/2,-drawHeight/2,drawWidth,drawHeight);}context.restore();
  }

  async function findStyle(card){const name=card.querySelector('h3')?.textContent.trim();const data=await fetch('/v1/hairstyles').then(r=>r.json());return data.items.find(item=>item.name===name)||data.items[0];}
  document.addEventListener('click',async event=>{const button=event.target.closest('.try-button');if(!button)return;event.preventDefault();event.stopImmediatePropagation();await openEditor(await findStyle(button.closest('.result-card')));},true);
  dialog.querySelector('.overlay-close').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});dialog.querySelectorAll('.view-tab').forEach(tab=>tab.addEventListener('click',()=>setView(tab.dataset.view)));
  [['#overlay-scale','scale',v=>v/100,'#scale-value',v=>`${v}%`],['#overlay-rotation','rotation',Number,'#rotation-value',v=>`${v}°`],['#overlay-opacity','opacity',v=>v/100,'#opacity-value',v=>`${v}%`]].forEach(([selector,key,convert,valueSelector,format])=>dialog.querySelector(selector).addEventListener('input',event=>{states[activeView][key]=convert(event.target.value);dialog.querySelector(valueSelector).textContent=format(event.target.value);render();}));
  dialog.querySelectorAll('[data-dx]').forEach(button=>button.addEventListener('click',()=>{states[activeView].x+=Number(button.dataset.dx)/100;states[activeView].y+=Number(button.dataset.dy)/100;render();}));
  dialog.querySelector('[data-reset-position]').addEventListener('click',()=>{const a=anchors[activeView];states[activeView].x=a.center_x;states[activeView].y=a.hairline_y;render();});
  dialog.querySelectorAll('.overlay-color').forEach(button=>button.addEventListener('click',()=>{states[activeView].color=button.dataset.color;syncControls();render();}));
  dialog.querySelector('[data-reset]').addEventListener('click',()=>{resetView(activeView);syncControls();render();});
  canvas.addEventListener('pointerdown',event=>{dragging=true;pointer={x:event.clientX,y:event.clientY};canvas.setPointerCapture(event.pointerId);});canvas.addEventListener('pointermove',event=>{if(!dragging)return;const rect=canvas.getBoundingClientRect();states[activeView].x+=(event.clientX-pointer.x)/rect.width;states[activeView].y+=(event.clientY-pointer.y)/rect.height;pointer={x:event.clientX,y:event.clientY};render();});canvas.addEventListener('pointerup',()=>dragging=false);canvas.addEventListener('pointercancel',()=>dragging=false);
  function download(view){setView(view);requestAnimationFrame(()=>canvas.toBlob(blob=>{const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`trimcircle-${selectedStyle.id}-${view}.jpg`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);},'image/jpeg',.9));}
  dialog.querySelector('[data-download]').addEventListener('click',()=>download(activeView));dialog.querySelector('[data-download-all]').addEventListener('click',()=>VIEWS.forEach((view,index)=>setTimeout(()=>download(view),index*450)));
})();
