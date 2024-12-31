module.exports = {
  darkMode: false, // Disable prefers-color-scheme
  content: [
    './templates/**/*.html',
    './static/js/**/*.js',
    './react-modal/src/**/*.{js,jsx,ts,tsx}',
    './static/css/**/*.css',
    './node_modules/@radix-ui/react-dialog/dist/*.js',
  ],
  theme: {
    extend: {
      fontFamily: {
        sohne: ['"sohne"', 'sans-serif'],
        sans: ['"sohne"', 'sans-serif'],
      },
      height: {
        'custom-mobile': '60vh',
        'custom-desktop': 'calc(100vh - 7.5rem)',
      },
    },
  },
  plugins: [],
};