'use strict';
const $ = id => document.getElementById(id);
let base = '', key = '', pending = false, connected = false;
let saved = null;
try { saved = JSON.parse(sessionStorage.getItem('mi-remote') || 'null'); } catch {}
$('bridge').value = saved?.base || (location.hostname.endsWith('github.io') ? '' : location.origin);
$('token').value = saved?.key || '';
function setConnected(value) { connected = value; $('controls').disabled = !value; $('status').textContent = value ? 'Συνδεδεμένο με το Mi Box' : 'Δεν έχει συνδεθεί'; $('status').classList.toggle('connected', value); }
function config() {
  const url = new URL($('bridge').value.trim());
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw Error('Βάλε διεύθυνση όπως http://192.168.1.10:8787 χωρίς διαδρομή.');
  base = url.origin; key = $('token').value.trim();
  if (!key) throw Error('Βάλε το κλειδί γέφυρας από το terminal.');
  if (location.protocol === 'https:' && url.protocol === 'http:') {
    $('localLink').href = base; $('localLink').hidden = false;
    throw Error('Για σύνδεση από GitHub Pages χρειάζεται γέφυρα HTTPS με έμπιστο πιστοποιητικό. Αλλιώς άνοιξε το τοπικό τηλεχειριστήριο από τον σύνδεσμο παρακάτω.');
  }
  $('localLink').hidden = true;
  try { sessionStorage.setItem('mi-remote', JSON.stringify({base, key})); } catch {}
}
async function api(path, data) {
  let response;
  try { response = await fetch(base + '/api/' + path, {method:data === undefined ? 'GET':'POST', headers:{Authorization:'Bearer '+key, ...(data === undefined ? {}:{'Content-Type':'application/json'})}, body:data === undefined ? undefined:JSON.stringify(data), signal:AbortSignal.timeout(22000)}); }
  catch { setConnected(false); throw Error('Δεν φτάνω στη γέφυρα. Έλεγξε διεύθυνση, δίκτυο, HTTPS και ότι τρέχει στον υπολογιστή.'); }
  const result = await response.json();
  if (!response.ok) { if (response.status === 401 || response.status === 409 || response.status >= 500) setConnected(false); throw Error(result.error || 'Η εντολή απέτυχε.'); }
  if ('connected' in result) setConnected(result.connected);
  return result;
}
async function run(fn) {
  if (pending) return;
  pending = true; $('message').textContent = 'Περίμενε…';
  try { await fn(); $('message').textContent = ''; }
  catch(error) { $('message').textContent = error.message; }
  finally { pending = false; }
}
$('settingsToggle').onclick = () => { $('settings').open = !$('settings').open; };
$('config').onsubmit = event => { event.preventDefault(); run(async () => {setConnected(false); config(); await api('connect', {}); $('settings').open = false;}); };
$('pair').onclick = () => run(async () => {setConnected(false); config(); await api('pair-start', {}); $('pairForm').hidden = false; $('code').focus();});
$('pairForm').onsubmit = event => {event.preventDefault(); run(async () => {await api('pair-finish', {code:$('code').value}); $('pairForm').hidden = true; $('code').value = ''; $('settings').open = false;});};
document.querySelectorAll('[data-key],[data-app]').forEach(button => button.onclick = () => run(async () => {
  await api(button.dataset.key ? 'key':'app', {value:button.dataset.key || button.dataset.app});
  if (navigator.vibrate) navigator.vibrate(12);
}));
const mapping = {ArrowUp:'DPAD_UP',ArrowDown:'DPAD_DOWN',ArrowLeft:'DPAD_LEFT',ArrowRight:'DPAD_RIGHT',Enter:'DPAD_CENTER',Escape:'BACK',' ':'MEDIA_PLAY_PAUSE'};
document.addEventListener('keydown', event => { if (!connected || event.repeat || /INPUT|BUTTON|SUMMARY|TEXTAREA/.test(event.target.tagName)) return; if (mapping[event.key]) {event.preventDefault(); run(() => api('key', {value:mapping[event.key]}));} });
setInterval(() => { if (base && key && !pending && !document.hidden) api('status').catch(error => {$('message').textContent = error.message;}); }, 5000);
