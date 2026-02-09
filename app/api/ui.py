from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'/>
  <title>RunTech MK1</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; max-width: 960px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    input, select, button { padding: 8px; margin: 4px 0; }
    pre { background: #f7f7f7; padding: 12px; border-radius: 8px; overflow: auto; }
  </style>
</head>
<body>
  <h1>RunTech MK1 — Daily Decision System</h1>

  <div class='card'>
    <h3>1) Sync from Strava</h3>
    <input id='token' type='password' placeholder='Strava access token' style='width: 420px;' />
    <button onclick='syncNow()'>Sync</button>
  </div>

  <div class='card'>
    <h3>2) Current State</h3>
    <button onclick='loadState()'>Refresh State</button>
  </div>

  <div class='card'>
    <h3>3) Recommendation</h3>
    <select id='phase'>
      <option>base</option><option selected>build</option><option>peak</option><option>taper</option>
    </select>
    <button onclick='recommend()'>Get Recommendation</button>
  </div>

  <div class='card'>
    <h3>4) Explain</h3>
    <input id='question' type='text' placeholder='Why am I tired?' style='width: 420px;' />
    <button onclick='explain()'>Ask</button>
  </div>

  <pre id='out'>Ready.</pre>

<script>
async function call(url, opts={}) {
  const r = await fetch(url, opts);
  const data = await r.json();
  document.getElementById('out').textContent = JSON.stringify(data, null, 2);
}
async function syncNow() {
  const t = document.getElementById('token').value;
  await call(`/sync?access_token=${encodeURIComponent(t)}`, {method: 'POST'});
}
async function loadState() { await call('/state'); }
async function recommend() {
  const p = document.getElementById('phase').value;
  await call(`/recommendation?phase=${encodeURIComponent(p)}`);
}
async function explain() {
  const q = document.getElementById('question').value;
  await call('/explain', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:q})});
}
</script>
</body>
</html>
"""
