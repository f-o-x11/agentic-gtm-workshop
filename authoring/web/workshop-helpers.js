/* Company inputs stay in this browser. No keys, uploads or network requests. */
(() => {
  const tokens = {
    website: '[YOUR_COMPANY_WEBSITE]', buyer: '[BUYER_SEGMENT]', offer: '[COLD_OFFER]',
    targetOne: '[TARGET_1_DOMAIN]', targetTwo: '[TARGET_2_DOMAIN]'
  };
  let fields = {};
  try { fields = JSON.parse(localStorage.getItem('gtm-part1-company') || '{}'); } catch {}
  const originals = new WeakMap();
  const render = text => Object.entries(tokens).reduce((out, [key, token]) => {
    const value = String(fields[key] || '').trim().replace(/[\r\n]+/g, ' ');
    return value ? out.split(token).join(value) : out;
  }, text);
  function attachPrompt(el, text) {
    originals.set(el, text);
    el.dataset.customPrompt = 'true';
    update();
  }
  function update() {
    document.querySelectorAll('[data-company-field]').forEach(el => {
      if (document.activeElement !== el) el.value = fields[el.dataset.companyField] || '';
    });
    document.querySelectorAll('[data-custom-prompt]').forEach(el => {
      const text = render(originals.get(el) || '');
      if (el.tagName === 'TEXTAREA') el.value = text; else el.textContent = text;
    });
  }
  document.querySelectorAll('[data-company-field]').forEach(el => {
    el.value = fields[el.dataset.companyField] || '';
    el.addEventListener('input', () => {
      fields[el.dataset.companyField] = el.value;
      try { localStorage.setItem('gtm-part1-company', JSON.stringify(fields)); } catch {}
      update();
    });
  });
  document.querySelectorAll('[data-personalize]').forEach(el => attachPrompt(el,
    el.tagName === 'TEXTAREA' ? el.value : el.textContent));
  window.addEventListener('storage', event => {
    if (event.key !== 'gtm-part1-company') return;
    try { fields = JSON.parse(event.newValue || '{}'); update(); } catch {}
  });
  function celebrate(label) {
    document.getElementById('workshop-celebration')?.remove();
    const layer = document.createElement('div');
    layer.id = 'workshop-celebration'; layer.className = 'workshop-confetti';
    layer.setAttribute('aria-hidden', 'true');
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
      for (let n = 0; n < 64; n++) {
        const piece = document.createElement('i');
        piece.style.setProperty('--x', `${Math.random() * 100}vw`);
        piece.style.setProperty('--drift', `${Math.random() * 150 - 75}px`);
        piece.style.setProperty('--delay', `${Math.random() * .25}s`);
        piece.style.setProperty('--turn', `${Math.random() * 720 - 360}deg`);
        piece.style.background = ['#ed5c2b', '#327d68', '#e4b858', '#9fc9b4'][n % 4];
        layer.append(piece);
      }
    }
    document.body.append(layer);
    const status = document.getElementById('workshop-success');
    if (status) { status.textContent = label; status.classList.add('visible'); }
    setTimeout(() => { layer.remove(); status?.classList.remove('visible'); }, 2300);
  }
  document.querySelectorAll('[data-exercise-complete]').forEach(button => {
    button.addEventListener('click', () => {
      button.textContent = '✓ I checked this result';
      button.setAttribute('aria-pressed', 'true');
      try { localStorage.setItem('gtm-part1-checked-' + button.dataset.exerciseComplete, 'true'); } catch {}
      celebrate('Result checked. Continue when the presenter is ready.');
    });
  });
  // Native dialogs keep keyboard/Escape behavior. A click on the backdrop closes them.
  document.querySelectorAll('dialog').forEach(dialog => dialog.addEventListener('click', event => {
    const box = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < box.left || event.clientX > box.right ||
        event.clientY < box.top || event.clientY > box.bottom)) dialog.close();
  }));
  document.querySelectorAll('[data-open-glossary]').forEach(button => button.addEventListener('click', () => {
    document.getElementById('glossary-dialog').showModal();
  }));
  document.querySelectorAll('[data-close-glossary]').forEach(button => button.addEventListener('click', () => {
    document.getElementById('glossary-dialog').close();
  }));
  window.GTMWorkshop = { attachPrompt, render, celebrate };
})();
