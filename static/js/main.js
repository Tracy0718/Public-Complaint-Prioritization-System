// AJAX submit with fetch and small UX improvements
document.addEventListener('DOMContentLoaded', ()=> {
  const form = document.getElementById('complaintForm');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.classList.add('is-loading');
    const fd = new FormData(form);
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    try {
      const res = await fetch(form.action, {method:'POST', headers:{'X-CSRFToken':csrftoken, 'X-Requested-With':'XMLHttpRequest'}, body: fd});
      const data = await res.json();
      if (data.status === 'success' || data.status === 'ok' || data.ok === true) {
        const el = document.getElementById('result');
        const cid = data.id || data.complaint_id || '';
        el.innerHTML = `
          <div class="result-card glass fx-card is-in" data-tilt="6">
            <div class="result-title">Complaint submitted</div>
            <div class="result-grid">
              <div class="result-item"><div class="result-k">Category</div><div class="result-v">${data.category}</div></div>
              <div class="result-item"><div class="result-k">Priority</div><div class="result-v">${data.priority}</div></div>
              <div class="result-item"><div class="result-k">Reference</div><div class="result-v">${cid || '—'}</div></div>
            </div>
            <div class="result-actions">
              <a class="btn btn-sm btn-outline-light btn-soft" href="/dashboard/">Go to dashboard</a>
              <button type="button" class="btn btn-sm btn-cta btn-glow" id="submitAnother">Submit another</button>
            </div>
          </div>
        `;
        if (window.toast) window.toast(`AI classified this as <strong>${data.category}</strong> with <strong>${data.priority}</strong> priority.`, { level: 'success', title: 'Submitted' });
        form.reset();
        document.getElementById('submitAnother')?.addEventListener('click', () => {
          document.getElementById('result').innerHTML = '';
          document.getElementById('complaintStudio')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, { once: true });
      } else {
        let msg = 'Error submitting complaint.';
        if (data.errors) {
          const parts = [];
          for (const [field, errs] of Object.entries(data.errors)) {
            parts.push(`${field}: ${errs.join(' ')}`);
          }
          if (parts.length) {
            msg += ' ' + parts.join(' | ');
          }
        }
        document.getElementById('result').innerHTML = `<div class="result-error">${msg}</div>`;
        if (window.toast) window.toast(msg, { level: 'danger', title: 'Submission failed' });
      }
    } catch (err) {
      document.getElementById('result').innerHTML = `<div class="result-error">Network error. Try again.</div>`;
      if (window.toast) window.toast('Network error. Try again.', { level: 'danger', title: 'Network' });
    } finally { btn.disabled = false; }
    btn.classList.remove('is-loading');
  });
});
