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

    // fetch.resetMocks();
    fetch.mockResponse(
        JSON.stringify({stuff: 'nonsense'})
    );

    let client = new LangQc();
    // No internet used!
    test('Data in comes straight out again', () => {
        let response = client.getInboxPromise();
        console.log(response);
        expect(response).resolves.toStrictEqual({
            stuff: 'nonsense'
        });

        expect(fetch.mock.calls.length).toEqual(1);

        // First fetch call, first element is URL, second is a header object
        expect(
            fetch.mock.calls[0][0]
        ).toEqual(
            '/api/pacbio/wells?qc_status=inbox&page_size=10&page_number=1'
        );

        // We can also test any custom header setting here
    });

    test('Posting', () => {
        fetch.mockResolvedValue(
            new Promise( () => {
                return JSON.stringify({
                    "user": "zx80@example.com",
                    "qc_type": "library",
                    "state": "Claimed",
                    "is_preliminary": true,
                    "created_by": "qc_user",
                })
            })
        )

        client.claimWell('TRACTION-RUN-299', 'B1');

        let request = fetch.mock.calls[1];
        expect(
            request[0]
        ).toEqual(
            '/api/pacbio/run/TRACTION-RUN-299/well/B1/qc_claim'
        );

        expect(
            request[1].method
        ).toEqual(
            'POST'
        );

        expect(
            JSON.parse(request[1].body)
            // Can we get a JSON response from this mock response?
        ).toStrictEqual(
            {qc_type: 'sequencing'}
        );
    });

    test('Fetch convenience functions send requests to...', () => {
        // Note that the mock remembers all calls until reset
        client.getClientConfig();
        expect(fetch.mock.calls[2][0]).toEqual('/api/config');

        client.getRunWellPromise('blah', 'A2');
        expect(fetch.mock.calls[3][0]).toEqual('/api/pacbio/run/blah/well/A2');
    });
    // mockFetch.resetMocks();
});

describe('URL generation' , () => {
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
