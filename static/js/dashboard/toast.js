// static/js/dashboard/toast.js

class Toast {
    constructor() {
      this.container = document.getElementById('toast-container');
  
      // Create the container dynamically if it doesn't exist
      if (!this.container) {
        this.container = document.createElement('div');
        this.container.id = 'toast-container';
        this.container.className = 'fixed bottom-4 left-4 z-50 space-y-2';
        document.body.appendChild(this.container);
      }
    }
  
    showToast(message, type = 'success', duration = 3000) {
        // Create the toast element
        const toast = document.createElement('div');
        toast.className = `toast-message flex items-center min-w-80 p-4 text-gray-500 bg-white rounded-lg shadow dark:text-gray-400 dark:bg-gray-800 animate-fade-in`;
      
        // Toast icon container
        const iconContainer = document.createElement('div');
        iconContainer.className = `inline-flex items-center justify-center flex-shrink-0 w-8 h-8 ${
          type === 'success'
            ? 'text-green-500 bg-green-100 dark:bg-green-800 dark:text-green-200'
            : 'text-red-500 bg-red-100 dark:bg-red-800 dark:text-red-200'
        } rounded-lg`;
      
        // Toast icon
        const icon = document.createElement('span');
        icon.innerHTML = this.getIcon(type);
      
        // Append icon to container
        iconContainer.appendChild(icon);
      
        // Toast message
        const messageEl = document.createElement('span');
        messageEl.textContent = message;
        messageEl.className = 'flex-grow ms-3 fm-inter text-sm';
      
        // Close button
        const closeButton = document.createElement('button');
        closeButton.className =
          'ms-auto -mx-1.5 -my-1.5 bg-white text-gray-400 hover:text-gray-900 rounded-lg focus:ring-2 focus:ring-gray-300 p-1.5 hover:bg-gray-100 inline-flex items-center justify-center h-8 w-8 dark:text-gray-500 dark:hover:text-white dark:bg-gray-800 dark:hover:bg-gray-700';
        closeButton.innerHTML =
          '<svg class="w-3 h-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14"><path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"></path></svg>';
        closeButton.onclick = () => this.dismissToast(toast);
      
        // Append elements
        toast.appendChild(iconContainer);
        toast.appendChild(messageEl);
        toast.appendChild(closeButton);
        this.container.appendChild(toast);
      
        // Auto-dismiss with fade-out animation
        setTimeout(() => {
          toast.classList.remove('animate-fade-in');
          toast.classList.add('animate-fade-out');
          toast.addEventListener('animationend', () => toast.remove());
        }, duration);
      }      
  
    dismissToast(toast) {
      toast.classList.add('animate-fade-out');
      toast.addEventListener('animationend', () => toast.remove());
    }
  
    getIcon(type) {
      if (type === 'success') {
        return '<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>';
      } else if (type === 'error') {
        return '<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M12 19c-3.866 0-7-3.134-7-7s3.134-7 7-7 7 3.134 7 7-3.134 7-7 7z"/></svg>';
      }
      return '';
    }
  }
  
  // Export the Toast class
  export const toast = new Toast();
  