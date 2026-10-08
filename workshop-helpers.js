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
  // Participants confirm their local results. Copying a prompt never confirms a result.
  const resultButtons = [...document.querySelectorAll('[data-exercise-complete]')];
  const checkpoints = [...document.querySelectorAll('[data-chapter-checkpoint]')];
  const savedState = new Map();
  const checkedKey = id => 'gtm-part1-checked-' + id;
  const finishedKey = chapter => 'gtm-part1-finished-chapter-' + chapter;
  function isSaved(key) {
    try { return localStorage.getItem(key) === 'true'; }
    catch { return savedState.get(key) === true; }
  }
  function save(key, value) {
    savedState.set(key, value);
    try { if (value) localStorage.setItem(key, 'true'); else localStorage.removeItem(key); } catch {}
  }
  function requiredResults(panel) { return JSON.parse(panel.dataset.requiredExercises); }
  function updateCompletion() {
    resultButtons.forEach(button => {
      const checked = isSaved(checkedKey(button.dataset.exerciseComplete));
      button.setAttribute('aria-pressed', String(checked));
      button.textContent = checked ? '✓ I checked this result' : 'My result matches these checks ✓';
    });
    checkpoints.forEach(panel => {
      const required = requiredResults(panel);
      const count = required.filter(id => isSaved(checkedKey(id))).length;
      const ready = count === required.length;
      const chapter = panel.dataset.chapterCheckpoint;
      if (!ready) save(finishedKey(chapter), false);
      const finished = ready && isSaved(finishedKey(chapter));
      const button = panel.querySelector('[data-finish-chapter]');
      button.disabled = !ready || finished;
      button.textContent = finished ? `Chapter ${chapter} complete ✓` : `Finish chapter ${chapter}`;
      panel.querySelector('[data-chapter-status]').textContent = finished
        ? 'All exercise results confirmed. Chapter complete.'
        : `${count} of ${required.length} exercise results confirmed. Check each result before finishing.`;
    });
  }
  resultButtons.forEach(button => button.addEventListener('click', () => {
    const key = checkedKey(button.dataset.exerciseComplete);
    save(key, !isSaved(key));
    updateCompletion();
  }));
  checkpoints.forEach(panel => panel.querySelector('[data-finish-chapter]').addEventListener('click', () => {
    const chapter = panel.dataset.chapterCheckpoint;
    const ready = requiredResults(panel).every(id => isSaved(checkedKey(id)));
    if (!ready || isSaved(finishedKey(chapter))) { updateCompletion(); return; }
    save(finishedKey(chapter), true);
    updateCompletion();
    celebrate(`Chapter ${chapter} complete. All exercise results confirmed.`);
  }));
  window.addEventListener('storage', event => {
    if (event.key?.startsWith('gtm-part1-checked-') || event.key?.startsWith('gtm-part1-finished-chapter-') || event.key === null) updateCompletion();
  });
  updateCompletion();
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
  window.GTMWorkshop = { attachPrompt, render };
})();
