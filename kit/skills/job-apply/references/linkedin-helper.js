/*
 * linkedin-helper.js - read-only page helper for LinkedIn Easy Apply (job-agent-kit).
 *
 * Run the whole file once per page load with the Claude in Chrome JavaScript tool; the last
 * expression returns "jobHelper ready ...". Then call:
 *   jobHelper.inspect()     visible fields in the Easy Apply dialog: label, type, required,
 *                           current value, options, validation error; plus step title, progress,
 *                           visible buttons and whether "Follow company" is ticked.
 *   jobHelper.exposeFile()  make the hidden <input type="file"> visible so find/read_page can
 *                           return its ref for the file-upload tool.
 * Outside a dialog both functions fall back to the page's form, so they also help on Dice and Indeed.
 * By design there is no click, fill or submit function: filling happens through visible tool
 * actions, and the final submit is always a separate, deliberate step.
 */
(() => {
  const DIALOG_SELECTORS = [
    '.jobs-easy-apply-modal',
    '[data-test-modal][role="dialog"]',
    '[role="dialog"]',
    '[aria-modal="true"]',
  ];
  const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();

  function visible(el) {
    if (!(el instanceof Element)) return false;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }

  function scope() {
    for (const sel of DIALOG_SELECTORS) {
      const hit = [...document.querySelectorAll(sel)].find(
        (n) => visible(n) && n.querySelector('input, select, textarea, button')
      );
      if (hit) return { root: hit, kind: 'dialog' };
    }
    const form = [...document.querySelectorAll('form')].find((f) => visible(f) && f.querySelector('input, select, textarea'));
    return form ? { root: form, kind: 'form' } : { root: document.body, kind: 'page' };
  }

  function labelFor(el, root) {
    if (el.id) {
      const l = root.querySelector(`label[for="${CSS.escape(el.id)}"]`) || document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (l && clean(l.innerText)) return clean(l.innerText);
    }
    const by = el.getAttribute('aria-labelledby');
    if (by) {
      const t = by.split(/\s+/).map((id) => document.getElementById(id)).filter(Boolean).map((n) => n.innerText).join(' ');
      if (clean(t)) return clean(t);
    }
    if (el.getAttribute('aria-label')) return clean(el.getAttribute('aria-label'));
    const wrap = el.closest('label');
    if (wrap && clean(wrap.innerText)) return clean(wrap.innerText);
    const fs = el.closest('fieldset');
    const legend = fs && fs.querySelector('legend');
    if (legend && clean(legend.innerText)) return clean(legend.innerText);
    const group = el.closest('[class*="form-element"], [class*="form-component"], [class*="grouping"], [class*="question"]');
    const glabel = group && group.querySelector('label, legend, [class*="label"], [class*="title"]');
    if (glabel && clean(glabel.innerText)) return clean(glabel.innerText);
    return clean(el.getAttribute('placeholder') || el.name || '');
  }

  function errorFor(el) {
    const group = el.closest('[class*="form-element"], [class*="form-component"], [class*="grouping"], fieldset');
    const err = group && group.querySelector('[class*="error"], [role="alert"]');
    return err ? clean(err.innerText) : '';
  }

  const requiredMark = (label) => /\*\s*$|\brequired\b/i.test(label);

  function inspect() {
    const { root, kind } = scope();
    const fields = [];
    const radioGroups = new Set();
    for (const el of root.querySelectorAll('input, select, textarea')) {
      const type = (el.type || el.tagName).toLowerCase();
      if (type === 'hidden' || type === 'submit' || type === 'button') continue;
      if (type === 'file') {
        fields.push({ type: 'file', label: labelFor(el, root), visible: visible(el), accept: el.accept || '',
          files: [...(el.files || [])].map((f) => f.name) });
        continue;
      }
      if (type === 'radio') {
        if (!el.name || radioGroups.has(el.name)) continue;
        radioGroups.add(el.name);
        const group = [...root.querySelectorAll(`input[type="radio"][name="${CSS.escape(el.name)}"]`)];
        const fs = el.closest('fieldset');
        const legend = fs && fs.querySelector('legend');
        const label = legend ? clean(legend.innerText) : labelFor(el, root);
        const checked = group.find((r) => r.checked);
        const radio = { type: 'radio', label, required: group.some((r) => r.required) || requiredMark(label),
          value: checked ? labelFor(checked, root) : '', options: group.map((r) => labelFor(r, root)) };
        const radioError = errorFor(el);
        if (radioError) radio.error = radioError;
        fields.push(radio);
        continue;
      }
      if (type !== 'checkbox' && !visible(el)) continue;
      const label = labelFor(el, root);
      const field = { type: el.tagName === 'SELECT' ? 'select' : type, label,
        required: el.required || el.getAttribute('aria-required') === 'true' || requiredMark(label) };
      if (type === 'checkbox') field.value = el.checked;
      else if (el.tagName === 'SELECT') {
        field.value = el.selectedIndex >= 0 ? clean(el.options[el.selectedIndex].text) : '';
        field.options = [...el.options].map((o) => clean(o.text)).slice(0, 30);
      } else field.value = el.value;
      const error = errorFor(el);
      if (error) field.error = error;
      fields.push(field);
    }
    const heading = root.querySelector('h1, h2, h3');
    const bar = root.querySelector('[role="progressbar"], progress');
    const buttons = [...root.querySelectorAll('button')].filter(visible)
      .map((b) => clean(b.innerText) || clean(b.getAttribute('aria-label'))).filter(Boolean);
    const follow = [...root.querySelectorAll('input[type="checkbox"]')].find((c) => /follow/i.test(labelFor(c, root)));
    return {
      scope: kind,
      step: heading ? clean(heading.innerText) : '',
      progress: bar ? String(bar.getAttribute('aria-valuenow') || bar.value || '') : '',
      fields,
      missingRequired: fields.filter((f) => f.required && (f.value === '' || f.value === false)).map((f) => f.label),
      buttons,
      followCompanyChecked: follow ? follow.checked : null,
    };
  }

  function exposeFile() {
    const { root, kind } = scope();
    let inputs = [...root.querySelectorAll('input[type="file"]')];
    if (!inputs.length && kind !== 'page') inputs = [...document.querySelectorAll('input[type="file"]')];
    if (!inputs.length) {
      return { ok: false, error: 'No file input found. On LinkedIn, open the resume step first (the input appears with "Upload resume").' };
    }
    inputs.forEach((el, i) => {
      el.removeAttribute('hidden');
      el.classList.remove('hidden', 'visually-hidden', 'sr-only');
      Object.assign(el.style, { display: 'block', visibility: 'visible', opacity: '1', position: 'static',
        width: 'auto', height: 'auto', clip: 'auto', clipPath: 'none', pointerEvents: 'auto' });
      if (!el.getAttribute('aria-label')) el.setAttribute('aria-label', `file upload input ${i + 1}`);
      el.dataset.jobHelper = `file-${i + 1}`;
    });
    inputs[0].scrollIntoView({ block: 'center' });
    return { ok: true, count: inputs.length, inputs: inputs.map((el, i) => ({
      marker: `file-${i + 1}`, label: labelFor(el, root), accept: el.accept || '', name: el.name || '', id: el.id || '' })) };
  }

  window.jobHelper = { inspect, exposeFile, version: '1.0' };
  return 'jobHelper ready: jobHelper.inspect(), jobHelper.exposeFile()';
})();
