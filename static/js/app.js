(() => {
  const audio = document.getElementById('audio-preview');
  const title = document.getElementById('player-title');
  const artist = document.getElementById('player-artist');
  const art = document.getElementById('player-art');
  const toggle = document.getElementById('player-toggle');
  const status = document.getElementById('player-status');
  const open = document.getElementById('open-spotify');
  let queue = [];
  let index = -1;
  let active = null;

  const escapeHtml = value => String(value || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const time = seconds => Number.isFinite(seconds) ? `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}` : '--:--';

  function chooseTrack(track, list = queue, at = index) {
    queue = list;
    index = at;
    active = track;
    title.textContent = track.name;
    artist.textContent = track.artists || 'Unknown artist';
    art.innerHTML = track.image ? `<img src="${escapeHtml(track.image)}" alt="">` : '<span>♪</span>';
    open.href = track.spotify_url || 'https://open.spotify.com';
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    toggle.disabled = !track.preview_url;
    toggle.textContent = '▶';
    status.textContent = track.preview_url ? '30 SEC PREVIEW' : 'PREVIEW UNAVAILABLE';
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('elapsed').textContent = '--:--';
    document.getElementById('duration').textContent = '--:--';
  }

  function playIndex(next) {
    if (!queue.length) return;
    const nextIndex = (next + queue.length) % queue.length;
    chooseTrack(queue[nextIndex], queue, nextIndex);
    if (active.preview_url) audio.play().then(() => { toggle.textContent = 'Ⅱ'; }).catch(() => { status.textContent = 'TAP PLAY TO START'; });
  }

  toggle.addEventListener('click', () => {
    if (!active || !active.preview_url) return;
    if (audio.paused) audio.play().then(() => { toggle.textContent = 'Ⅱ'; }).catch(() => { status.textContent = 'PREVIEW COULD NOT PLAY'; });
    else audio.pause();
  });
  audio.addEventListener('pause', () => { if (!audio.ended) toggle.textContent = '▶'; });
  audio.addEventListener('play', () => { toggle.textContent = 'Ⅱ'; });
  audio.addEventListener('timeupdate', () => {
    const pct = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
    document.getElementById('progress-fill').style.width = `${pct}%`;
    document.getElementById('elapsed').textContent = time(audio.currentTime);
    document.getElementById('duration').textContent = time(audio.duration);
  });
  audio.addEventListener('ended', () => playIndex(index + 1));
  document.getElementById('next-track').addEventListener('click', () => playIndex(index + 1));
  document.getElementById('previous-track').addEventListener('click', () => playIndex(index - 1));

  document.getElementById('save-current').addEventListener('click', async () => {
    if (!active) return;
    if (!window.MOODIFY.authenticated) { location.href = '/login/'; return; }
    const response = await fetch('/favorites/add/', {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':window.MOODIFY.csrf}, body:JSON.stringify(active)});
    const result = await response.json();
    status.textContent = result.ok ? 'SAVED TO FAVORITES' : (result.error || 'COULD NOT SAVE');
  });

  window.MoodifyApp = {
    chooseTrack,
    async recommend(params) {
      const section = document.getElementById('track-results');
      if (!section) { location.href = '/discover/?' + new URLSearchParams(params); return; }
      const titleNode = document.getElementById('results-title');
      const source = document.getElementById('result-source');
      titleNode.textContent = 'Finding your sound…';
      section.innerHTML = '<div class="loading-row"><span></span><span></span><span></span></div>';
      source.textContent = '';
      const query = new URLSearchParams(params);
      try {
        const response = await fetch(`/api/music/recommendations/?${query}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Music search is unavailable.');
        titleNode.textContent = `${data.mood} sounds like this.`;
        source.textContent = `LIVE RESULTS · ${data.source}`;
        renderTracks(data.tracks || [], section);
      } catch (error) {
        titleNode.textContent = 'We couldn’t reach your music.';
        section.innerHTML = `<div class="empty-state"><div class="empty-glyph">↻</div><h3>${escapeHtml(error.message)}</h3><p>Try again in a moment, or search directly in Spotify.</p><a class="button button-outline" href="https://open.spotify.com/search/${encodeURIComponent(query.toString())}" target="_blank" rel="noopener">Search Spotify ↗</a></div>`;
      }
    }
  };

  function renderTracks(tracks, container) {
    if (!tracks.length) { container.innerHTML='<div class="empty-state"><div class="empty-glyph">♫</div><h3>No tracks found this time.</h3><p>Try a different mood or search phrase.</p></div>'; return; }
    container.innerHTML = tracks.map((track, i) => `<article class="track-card"><button class="cover-button" data-play="${i}" aria-label="Play ${escapeHtml(track.name)} preview">${track.image ? `<img src="${escapeHtml(track.image)}" alt="Album art for ${escapeHtml(track.name)}" loading="lazy">` : '<span class="cover-placeholder">♪</span>'}<span class="cover-play">▶</span></button><div class="track-info"><strong title="${escapeHtml(track.name)}">${escapeHtml(track.name)}</strong><span>${escapeHtml(track.artists)}</span><small>${track.preview_url ? '30 second preview' : 'Preview not available'}</small></div><a class="track-open" href="${escapeHtml(track.spotify_url || 'https://open.spotify.com')}" target="_blank" rel="noopener" title="Open in Spotify">↗</a></article>`).join('');
    container.querySelectorAll('[data-play]').forEach(button => button.addEventListener('click', () => playIndex(Number(button.dataset.play))));
    queue = tracks;
  }
})();
