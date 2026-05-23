// activate_stab.js (workspace root)
const axios = require('axios');
(async () => {
  try {
    const res = await axios.post('http://localhost:3000/api/stab', { initiator: 'USER' });
    console.log('STAB activation response:', res.data);
  } catch (e) {
    console.error('Error activating STAB:', e.message);
  }
})();
