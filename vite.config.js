import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        artur: resolve(__dirname, 'artur.html'),
        synapse: resolve(__dirname, 'synapse.html'),
        trap: resolve(__dirname, 'trap.html')
      }
    }
  }
});
