console.log('PostCSS config loaded!');

module.exports = {
    plugins: [
      require('postcss-import'), // Handles @import directives
      require('tailwindcss'),   // Processes Tailwind classes
      require('autoprefixer'),  // Adds vendor prefixes for compatibility
    ],
  };  