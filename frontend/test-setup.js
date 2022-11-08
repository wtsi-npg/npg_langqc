import { fetch } from 'cross-fetch';
import createFetchMock from 'vitest-fetch-mock';
import { vi } from 'vitest';

global.fetch = fetch;
const fetchMock = createFetchMock(vi);

fetchMock.enableMocks();
