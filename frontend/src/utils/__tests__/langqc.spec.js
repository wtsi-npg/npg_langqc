import { describe, expect, test, vi } from 'vitest';
import LangQc from "../langqc.js";
import createFetchMock from 'vitest-fetch-mock';

describe('Constructing LangQC client', () => {
    test('Check default route setting', () => {
        let client = new LangQc();
        expect(client).toBeDefined();

        expect(client.getUrl('run').toString()).toEqual('/api/pacbio/run');
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
    // No internet used!
    test('Data in comes straight out again', () => {
        let response = client.getInboxPromise();
        expect(response).resolves.toBe({
            stuff: 'nonsense'
        });

        expect(fetch.mock.calls.length).toEqual(1);

        // First fetch call, first element is URL, second is a header object
        expect(
            fetch.mock.calls[0][0]
        ).toEqual(
            '/api/pacbio/wells?qc_status=inbox&weeks=1&page_size=10&page_number=1'
        );

        // We can also test any custom header setting here
    });

    test('Fetch convenience functions send requests to...', () => {
        // Note that the mock remembers all calls until reset
        client.getClientConfig();
        expect(fetch.mock.calls[1][0]).toEqual('/api/config');

        client.getRunWellPromise('blah', 'A2');
        expect(fetch.mock.calls[2][0]).toEqual('/api/pacbio/run/blah/well/A2');
    })
});

describe('URL generation' , () => {
    let client = new LangQc();

    test('buildUrl edges', () => {
        expect(client.buildUrl()).toEqual('/api/pacbio');

        expect(client.buildUrl('/wells/stuff')).toEqual('/api/pacbio/wells/stuff');

        expect(client.buildUrl('/wells', ['weeks=1'])).toEqual('/api/pacbio/wells?weeks=1');

        expect(client.buildUrl(['run', 'TRACTION-RUN-10', 'well', 'B1'])).toEqual('/api/pacbio/run/TRACTION-RUN-10/well/B1');
    });

    test('getUrl', () => {
        expect(client.getUrl('run')).toEqual('/api/pacbio/run')
    });
});
