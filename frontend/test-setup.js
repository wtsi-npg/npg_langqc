import { fetch } from 'cross-fetch';

// Provide a fetch API for when we're not testing in a browser
global.fetch = fetch;
