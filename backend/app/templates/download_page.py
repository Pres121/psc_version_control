"""Simple branded PSC download landing page (auto-starts download)."""

DOWNLOAD_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>PSC Update — Download</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet" />
<style>
  :root {
    --green: #0d9f6e;
    --green-dark: #066a48;
    --bg: #f3f6f9;
    --card: #ffffff;
    --text: #0b1220;
    --muted: #6b7a90;
    --border: #e6ebf1;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    color: var(--text);
    background:
      radial-gradient(ellipse 70% 50% at 90% 0%, rgba(13,159,110,.14), transparent 55%),
      radial-gradient(ellipse 50% 40% at 0% 100%, rgba(13,159,110,.08), transparent 50%),
      var(--bg);
  }
  .card {
    width: 100%;
    max-width: 440px;
    padding: 32px 28px;
    border: 1px solid var(--border);
    border-radius: 22px;
    background: var(--card);
    box-shadow: 0 20px 48px rgba(15, 23, 42, .08);
    text-align: center;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 18px;
    padding: 6px 12px;
    border-radius: 999px;
    background: #edfaf5;
    color: var(--green-dark);
    font-size: 12px;
    font-weight: 700;
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green);
    animation: pulse 1.6s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: .45; transform: scale(.85); }
  }
  h1 { font-size: 24px; font-weight: 800; letter-spacing: -.03em; margin-bottom: 8px; }
  .meta { color: var(--muted); font-size: 14px; margin-bottom: 22px; line-height: 1.5; }
  .meta strong { color: var(--text); }
  .notes {
    text-align: left;
    margin: 0 0 22px;
    padding: 14px 16px;
    border-radius: 14px;
    background: #f7f9fc;
    border: 1px solid var(--border);
    color: var(--muted);
    font-size: 13px;
  }
  .notes ul { margin: 8px 0 0 18px; color: var(--text); }
  button, .btn {
    display: inline-flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    gap: 10px;
    min-height: 48px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(145deg, var(--green), var(--green-dark));
    color: #fff;
    font: inherit;
    font-weight: 800;
    cursor: pointer;
    text-decoration: none;
    box-shadow: 0 8px 20px rgba(13,159,110,.28);
  }
  button:disabled { opacity: .65; cursor: wait; }
  .hint { margin-top: 14px; color: var(--muted); font-size: 12px; }
  .error {
    margin-top: 16px; padding: 12px 14px; border-radius: 12px;
    background: #fef1f1; color: #b42318; font-size: 13px; font-weight: 600;
  }
</style>
</head>
<body>
  <main class="card">
    <div class="badge"><span class="dot"></span> PSC Update Hub</div>
    <h1 id="title">Preparing download…</h1>
    <p class="meta" id="meta">Looking up the latest build for this app.</p>
    <div class="notes" id="notes" hidden></div>
    <button id="download-btn" type="button" disabled>Download</button>
    <p class="hint" id="hint">If the download does not start automatically, tap the button above.</p>
    <div class="error" id="error" hidden></div>
  </main>
  <script>
    const params = new URLSearchParams(window.location.search);
    const parts = window.location.pathname.split('/').filter(Boolean);
    const appKey = parts[parts.length - 1] || params.get('app');
    const platform = params.get('platform') || 'android';
    const apiBase = window.location.origin + '/api/v1';

    const titleEl = document.getElementById('title');
    const metaEl = document.getElementById('meta');
    const notesEl = document.getElementById('notes');
    const btn = document.getElementById('download-btn');
    const errorEl = document.getElementById('error');
    const hintEl = document.getElementById('hint');

    let downloadUrl = null;

    function startDownload(url) {
      const a = document.createElement('a');
      a.href = url;
      a.rel = 'noopener';
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      a.remove();
    }

    btn.addEventListener('click', () => {
      if (downloadUrl) startDownload(downloadUrl);
    });

    async function load() {
      if (!appKey) {
        titleEl.textContent = 'Missing app';
        metaEl.textContent = 'No app key was provided in the link.';
        errorEl.hidden = false;
        errorEl.textContent = 'Invalid download link.';
        return;
      }
      try {
        const res = await fetch(`${apiBase}/downloads/${encodeURIComponent(appKey)}?platform=${encodeURIComponent(platform)}`);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || 'Could not load download');

        titleEl.textContent = data.app_name;
        metaEl.innerHTML = `Version <strong>${data.version}</strong> · Build <strong>${data.build_number}</strong> · ${data.platform.toUpperCase()}`
          + (data.file_name ? `<br/>${data.file_name}` : '');

        if (Array.isArray(data.release_notes) && data.release_notes.length) {
          notesEl.hidden = false;
          notesEl.innerHTML = '<strong>What\\'s new</strong><ul>' +
            data.release_notes.map((n) => `<li>${String(n).replace(/</g,'&lt;')}</li>`).join('') +
            '</ul>';
        }

        downloadUrl = data.download_url;
        btn.disabled = false;
        btn.textContent = 'Download update';
        hintEl.textContent = 'Download starting… If nothing happens, tap the button.';
        startDownload(downloadUrl);
      } catch (err) {
        titleEl.textContent = 'Download unavailable';
        metaEl.textContent = 'We could not find a published build for this app.';
        errorEl.hidden = false;
        errorEl.textContent = err.message || 'Something went wrong';
        btn.disabled = true;
        btn.textContent = 'Unavailable';
      }
    }

    load();
  </script>
</body>
</html>
"""
