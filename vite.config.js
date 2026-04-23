const path = require('path');

module.exports = {
  build: {
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html'),
        artur: path.resolve(__dirname, 'artur.html'),
        synapse: path.resolve(__dirname, 'synapse.html'),
        trap: path.resolve(__dirname, 'trap.html')
      }
    }
  }
};
