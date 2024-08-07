import { describe, expect, test } from 'vitest';
import LangQc from "../langqc.js";

describe('Constructing LangQC client', () => {
    test('Check default route setting', () => {
        let client = new LangQc();
        expect(client).toBeDefined();

        expect(client.getUrl('run').toString()).toEqual('/api/pacbio/run');
    })
});

describe('Example fake remote api call', () => {

    const responseBody = { stuff: 'nonsense' }

    fetch.mockResponse(
        JSON.stringify(responseBody)
    );

    let client = new LangQc();
    // No internet used!
    test('Data in comes straight out again', () => {
        let response = client.getInboxPromise();
        expect(response).resolves.toStrictEqual(responseBody);

        expect(fetch.mock.calls.length).toEqual(1);

        // First fetch call, first element is URL, second is a header object
        expect(
            fetch.mock.calls[0][0]
        ).toEqual(
            '/api/pacbio/wells?qc_status=inbox&page_size=10&page_number=1'
        );

        expect(
            fetch.mock.calls[0][1].headers.Accept
        ).toEqual('application/json');

    });

    test('fetchWrapper correctly sets headers for posts and puts', () => {
        let requestBody = { data: true };
        let response = client.fetchWrapper('/place', 'POST', requestBody);
        expect(response).resolves.toStrictEqual(responseBody);

        expect(
            fetch.mock.calls[1][1].headers['Content-type']
        ).toEqual('application/json');

        expect(
            fetch.mock.calls[1][1].body
        ).toStrictEqual(JSON.stringify(requestBody));

        response = client.fetchWrapper('/place', 'PUT', requestBody);
        expect(response).resolves.toStrictEqual(responseBody);
    });

    test('Claiming with a POST', () => {
        fetch.mockResolvedValue(
            new Promise(() => {
                return JSON.stringify({
                    "user": "zx80@example.com",
                    "qc_type": "library",
                    "state": "Claimed",
                    "is_preliminary": true,
                    "created_by": "qc_user",
                })
            })
        )

        client.claimWell('ABCDEF');

        let request = fetch.mock.calls[3];
        expect(
            request[0]
        ).toEqual(
            '/api/pacbio/products/ABCDEF/qc_claim'
        );

        expect(
            request[1].method
        ).toEqual(
            'POST'
        );
    });

    test('Fetch convenience functions send requests to...', () => {
        // Note that the mock remembers all calls until reset
        client.getClientConfig();
        expect(fetch.mock.calls[4][0]).toEqual('/api/config');

        client.getWellPromise('A12345');
        expect(fetch.mock.calls[5][0]).toEqual('/api/pacbio/products/A12345/seq_level');

        client.getWellsForRunPromise('blah')
        expect(fetch.mock.calls[6][0]).toEqual('/api/pacbio/run/blah?page_size=100&page=1')

        client.getPoolMetrics('A12345');
        expect(fetch.mock.calls[7][0]).toEqual('/api/pacbio/products/A12345/seq_level/pool')
    });
});

describe('URL generation', () => {
    let client = new LangQc();

    test('buildUrl edges', () => {
        expect(client.buildUrl()).toEqual('/api/pacbio');

        expect(client.buildUrl('/wells/stuff')).toEqual('/api/pacbio/wells/stuff');

        expect(client.buildUrl('/wells', ['page_size=3', 'page_number=1'])).toEqual(
            '/api/pacbio/wells?page_size=3&page_number=1');

        expect(client.buildUrl(['run', 'TRACTION-RUN-10', 'well', 'B1'])).toEqual('/api/pacbio/run/TRACTION-RUN-10/well/B1');
    });

    test('getUrl', () => {
        expect(client.getUrl('run')).toEqual('/api/pacbio/run')
    });
});
