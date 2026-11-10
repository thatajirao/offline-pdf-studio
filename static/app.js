const tabs = document.querySelectorAll('.tab');
tabs.forEach(tab => tab.addEventListener('click', () => {
  tabs.forEach(t => t.classList.toggle('active', t === tab));
  ['convert','organize','images','security'].forEach(id => document.getElementById(id).classList.toggle('hidden', id !== tab.dataset.tab));
  showStatus('');
}));
function showStatus(message, type='') {
  const el = document.getElementById('status');
  el.textContent = message;
  el.className = 'status ' + type;
}
document.querySelectorAll('input[type=file]').forEach(input => input.addEventListener('change', () => {
  const label = input.closest('.drop');
  const files = [...input.files];
  if (files.length) label.querySelector('span').textContent = files.length === 1 ? files[0].name : files.length + ' files selected';
}));
document.querySelectorAll('form[data-endpoint]').forEach(form => form.addEventListener('submit', async e => {
  e.preventDefault();
  const btn = form.querySelector('button');
  const original = btn.innerHTML;
  btn.disabled = true;
  btn.textContent = 'Processing…';
  showStatus('Processing locally on this computer. Please wait…');
  try {
    const response = await fetch(form.dataset.endpoint, {method:'POST', body:new FormData(form)});
    const type = response.headers.get('content-type') || '';
    if (!response.ok || type.includes('application/json')) {
      const data = await response.json();
      throw new Error(data.error || 'Operation failed.');
    }
    const blob = await response.blob();
    const disposition = response.headers.get('content-disposition') || '';
    const match = disposition.match(/filename="?([^"]+)"?/i);
    const filename = match ? match[1] : 'download';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    const compressionResult = response.headers.get('X-Compression-Result');
    if (compressionResult) {
      const before = Number(response.headers.get('X-Original-Bytes') || 0);
      const after = Number(response.headers.get('X-Output-Bytes') || 0);
      const formatBytes = value => value < 1024 * 1024
        ? (value / 1024).toFixed(1) + ' KB'
        : (value / (1024 * 1024)).toFixed(2) + ' MB';
      if (compressionResult === 'unchanged') {
        showStatus('This PDF was already compact or could not be reduced. The original file was kept (' + formatBytes(before) + ').', 'success');
      } else {
        const percent = before > 0 ? Math.round((1 - after / before) * 100) : 0;
        showStatus('Compression complete: ' + formatBytes(before) + ' → ' + formatBytes(after) + ' (' + percent + '% smaller).', 'success');
      }
    } else {
      showStatus('Done! Your file has been created and downloaded.', 'success');
    }
    form.reset();
  } catch (err) {
    showStatus(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = original;
  }
}));
