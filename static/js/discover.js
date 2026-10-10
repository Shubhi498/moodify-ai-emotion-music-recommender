(() => {
  const form = document.getElementById('search-form');
  const results = document.getElementById('track-results');
  if (form) form.addEventListener('submit', async event => {
    event.preventDefault();
    const query = document.getElementById('search-query').value.trim();
    if (!query) return;
    document.getElementById('results-title').textContent = `Searching for “${query}”…`;
    results.innerHTML = '<div class="loading-row"><span></span><span></span><span></span></div>';
    try {
      const response = await fetch(`/api/music/search/?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Search unavailable.');
      document.getElementById('results-title').textContent = data.tracks.length ? `Results for “${query}”.` : 'No tracks found.';
      document.getElementById('results-eyebrow').textContent = 'SPOTIFY CATALOG SEARCH';
      document.getElementById('result-source').textContent = `LIVE RESULTS · ${data.source}`;
      render(data.tracks);
    } catch (error) { document.getElementById('results-title').textContent = 'Search unavailable.'; results.innerHTML = `<div class="empty-state"><div class="empty-glyph">↻</div><h3>${escape(error.message)}</h3><p>Check Spotify setup and try again.</p></div>`; }
  });

  document.querySelectorAll('.mood-select').forEach(button => button.addEventListener('click', () => MoodifyApp.recommend({emotion:button.dataset.emotion})));

  function escape(value) { return String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function render(tracks) {
    if (!tracks.length) { results.innerHTML='<div class="empty-state"><div class="empty-glyph">♫</div><h3>Nothing in the catalog matched.</h3><p>Try a different phrase.</p></div>'; return; }
    results.innerHTML = tracks.map((track,i) => `<article class="track-card"><button class="cover-button" data-play="${i}" aria-label="Play ${escape(track.name)} preview">${track.image?`<img src="${escape(track.image)}" alt="Album art for ${escape(track.name)}" loading="lazy">`:'<span class="cover-placeholder">♪</span>'}<span class="cover-play">▶</span></button><div class="track-info"><strong>${escape(track.name)}</strong><span>${escape(track.artists)}</span><small>${track.preview_url?'30 second preview':'Preview not available'}</small></div><a class="track-open" href="${escape(track.spotify_url||'https://open.spotify.com')}" target="_blank" rel="noopener" aria-label="Open in Spotify">↗</a></article>`).join('');
    results.querySelectorAll('[data-play]').forEach(button=>button.addEventListener('click',()=>MoodifyApp.chooseTrack(tracks[Number(button.dataset.play)],tracks,Number(button.dataset.play))));
  }

  const video=document.getElementById('camera-video');
  if (!video) return;
  let stream=null;
  const start=document.getElementById('start-camera');
  const capture=document.getElementById('capture-analyze');
  const stop=document.getElementById('stop-camera');
  const message=document.getElementById('camera-message');
  const placeholder=document.getElementById('camera-placeholder');
  const indicator=document.getElementById('camera-indicator');
  const result=document.getElementById('prediction-result');

  start.addEventListener('click',async()=>{
    if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){message.textContent='This browser does not support camera access. Use mood selection instead.';return;}
    try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user'},audio:false});video.srcObject=stream;placeholder.hidden=true;indicator.classList.add('on');indicator.innerHTML='<i></i> CAMERA ON';capture.disabled=false;stop.disabled=false;start.disabled=true;message.textContent='Camera is on. Center your face and capture when ready.';}
    catch(error){message.textContent=error.name==='NotAllowedError'?'Camera permission was denied. You can still choose a mood manually.':'Camera is unavailable. Check browser permission or choose a mood manually.';}
  });
  stop.addEventListener('click',stopCamera);
  function stopCamera(){if(stream)stream.getTracks().forEach(track=>track.stop());stream=null;video.srcObject=null;placeholder.hidden=false;indicator.classList.remove('on');indicator.innerHTML='<i></i> CAMERA OFF';capture.disabled=true;stop.disabled=true;start.disabled=false;message.textContent='Camera is off until you choose Start camera.';}
  capture.addEventListener('click',async()=>{
    if(!stream||!video.videoWidth){message.textContent='Wait for the camera preview, then try again.';return;}
    capture.disabled=true;message.textContent='Reading the frame…';result.hidden=true;
    const canvas=document.getElementById('camera-canvas');canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);
    canvas.toBlob(async blob=>{
      if(!blob){message.textContent='Could not capture the frame. Please retry.';capture.disabled=false;return;}
      const formData=new FormData();formData.append('image',blob,'camera.jpg');
      try{const response=await fetch('/api/emotion/predict/',{method:'POST',headers:{'X-CSRFToken':window.MOODIFY.csrf},body:formData});const data=await response.json();if(!response.ok)throw new Error(data.error||'Could not analyze that frame.');if(!data.ok){result.hidden=false;result.innerHTML=`<strong>One more try?</strong><span>${Math.round(data.confidence*100)}% confidence · ${data.message}</span>`;message.textContent=data.message;capture.disabled=false;return;}result.hidden=false;result.innerHTML=`<strong>${data.emotion[0].toUpperCase()+data.emotion.slice(1)} <span>· ${Math.round(data.confidence*100)}% estimate</span></strong><span>Suggested mood: ${data.music_mood}. You can choose another mood at any time.</span><button class="button button-primary" id="load-detected-mood">Find my soundtrack</button>`;document.getElementById('load-detected-mood').addEventListener('click',()=>MoodifyApp.recommend({emotion:data.emotion}));message.textContent='Prediction ready. Treat it as a suggestion.';capture.disabled=false;}
      catch(error){message.textContent=error.message;capture.disabled=false;}
    },'image/jpeg',0.86);
  });
  window.addEventListener('pagehide',stopCamera);
})();
