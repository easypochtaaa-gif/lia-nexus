const { defineConfig } = require('vite');
const { resolve } = require('path');

module.exports = defineConfig({
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
