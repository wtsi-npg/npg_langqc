import { describe, expect, test, vi } from 'vitest';
import LangQc from "../langqc.js";
import createFetchMock from 'vitest-fetch-mock';

describe('Constructing LangQC client', () => {
    test('Check default route setting', () => {
        let client = new LangQc();
        expect(client).toBeDefined();

        expect(client.getUrl('inbox').toString()).toEqual('/pacbio/inbox?weeks=1');
        expect(client.getUrl('run').toString()).toEqual('/pacbio/run');
    })
});

describe('Example fake remote api call', () => {
    const mockFetch = createFetchMock(vi);
    mockFetch.enableMocks();

    fetch.mockResolvedValue(
        new Promise( () => {
            return {stuff: 'nonsense'}
        })
    );

    let client = new LangQc();
    let response = client.getInboxPromise();
    // No internet used!
    test('Data in comes straight out again', () => {
        expect(response).resolves.toBe({
            stuff: 'nonsense'
        });

        expect(fetch.mock.calls.length).toEqual(1);
    });
});

describe('URL generation' , () => {
    let client = new LangQc();

    test('buildUrl edges', () => {
        expect(client.buildUrl()).toEqual('/pacbio');

        expect(client.buildUrl('/wells/stuff')).toEqual('/pacbio/wells/stuff');

        expect(client.buildUrl('/wells', ['weeks=1'])).toEqual('/pacbio/wells?weeks=1');

        expect(client.buildUrl(['run', 'TRACTION-RUN-10', 'well', 'B1'])).toEqual('/pacbio/run/TRACTION-RUN-10/well/B1');
    });

    test('getUrl', () => {
        expect(client.getUrl('run')).toEqual('/pacbio/run')
    });
});