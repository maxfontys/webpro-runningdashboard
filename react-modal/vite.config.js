import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { readdirSync, unlinkSync } from 'fs';
import { join } from 'path';

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'clean-dist-plugin',
      buildStart() {
        const distPath = join(__dirname, '../static/dist');
        try {
          const files = readdirSync(distPath);
          files.forEach((file) => {
            if (
              (file.endsWith('.js') || file.endsWith('.css')) && 
              file !== 'styles.css' // Keep styles.css intact
            ) {
              unlinkSync(join(distPath, file)); // Remove old JS and non-styles.css files
            }
          });
          console.log(`Cleaned old files in ${distPath} (excluding styles.css)`);
        } catch (err) {
          console.error(`Error cleaning dist directory: ${err.message}`);
        }
      },
    },
  ],
  build: {
    outDir: '../static/dist',
    assetsDir: '.',
    emptyOutDir: false, // Keep this false to prevent deleting the entire directory
    rollupOptions: {
      input: 'src/main.jsx',
    },
  },
});