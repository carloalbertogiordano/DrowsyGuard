// Config minima Node-RED per DrowsyGuard.
// functionGlobalContext espone 'crypto' (Node core, per decifrare AES-256-CBC
// nel Function node del flow) e 'aesKey' (letta da env var AES_KEY, mai
// hardcoded qui -- vedi docker-compose.yml + .env, gitignored).
module.exports = {
    flowFile: 'flows.json',
    uiPort: process.env.PORT || 1880,
    functionGlobalContext: {
        crypto: require('crypto'),
        aesKey: process.env.AES_KEY,
    },
};
