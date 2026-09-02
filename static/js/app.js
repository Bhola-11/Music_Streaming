/**
 * MusicVerse Master Frontend Controller
 * Manages CSRF tokens, AJAX helpers, drawer navigation, dropdowns, and UI state.
 */

// Helper to get Django CSRF Cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Global AJAX Setup
window.musicverseFetch = async function(url, options = {}) {
  const defaultHeaders = {
    'X-CSRFToken': getCookie('csrftoken'),
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
  };

  options.headers = { ...defaultHeaders, ...options.headers };
  return fetch(url, options);
};

// Social Follow Toggle Handler
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-action="toggle-follow"]').forEach(button => {
    button.addEventListener('click', async (e) => {
      e.preventDefault();
      const username = button.dataset.username;
      const url = `/accounts/users/${username}/toggle-follow/`;

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
          }
        });
        const data = await response.json();
        if (data.success) {
          if (data.is_following) {
            button.classList.remove('btn-secondary');
            button.classList.add('btn-primary');
            button.innerText = 'Following';
            Toast.success(`You are now following ${username}!`);
          } else {
            button.classList.remove('btn-primary');
            button.classList.add('btn-secondary');
            button.innerText = 'Follow';
            Toast.info(`Unfollowed ${username}`);
          }
          const followerCounter = document.getElementById(`followers-count-${username}`);
          if (followerCounter) {
            followerCounter.innerText = data.followers_count;
          }
        }
      } catch (err) {
        console.error('Follow error:', err);
        Toast.error('Network error. Please try again.');
      }
    });
  });
});
