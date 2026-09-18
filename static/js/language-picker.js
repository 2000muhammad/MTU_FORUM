(() => {
  const pickers = document.querySelectorAll('.language-picker');
  document.addEventListener('click', event => {
    pickers.forEach(picker => { if (!picker.contains(event.target)) picker.open = false; });
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') pickers.forEach(picker => {
      if (picker.open) { picker.open = false; picker.querySelector('summary').focus(); }
    });
  });
})();
