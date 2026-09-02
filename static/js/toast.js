/**
 * MusicVerse Dynamic Toast Alert System
 */
class ToastManager {
  constructor() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  }

  show(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast-message toast-${type}`;

    let icon = 'ℹ️';
    if (type === 'success') icon = '✓';
    if (type === 'error') icon = '⚠️';
    if (type === 'warning') icon = '⚡';

    toast.innerHTML = `
      <span style="font-size: 1.2rem; font-weight: bold;">${icon}</span>
      <div style="flex: 1;">${message}</div>
      <button style="background: none; border: none; color: #94A3B8; cursor: pointer; font-size: 1.1rem;" onclick="this.parentElement.remove()">✕</button>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  success(msg, dur) { this.show(msg, 'success', dur); }
  error(msg, dur) { this.show(msg, 'error', dur); }
  info(msg, dur) { this.show(msg, 'info', dur); }
  warning(msg, dur) { this.show(msg, 'warning', dur); }
}

window.Toast = new ToastManager();
