document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const button = form.querySelector('button[type="submit"]');
      if (button && !form.action.includes('/admin/delete/')) {
        button.disabled = true;
        button.textContent = 'Working…';
      }
    });
  });
});
