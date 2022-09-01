import { describe, expect, test, vi } from 'vitest';
import LangQc from "../langqc.js";
import createFetchMock from 'vitest-fetch-mock';


describe('Instantiate client', () => {
    test('No argument, no instance', () => {
        expect(() => { new LangQc() })
        .toThrowError('LangQc client must know where the web service is')
    })
});

describe('Constructing LangQC client', () => {
    test('Check route setting', () => {
        let client = new LangQc('https://niceplace.test');
        expect(client).toBeDefined();

        expect(client.getUrl('inbox').toString()).toEqual('https://niceplace.test/pacbio/inbox?weeks=1');
        expect(client.getUrl('run').toString()).toEqual('https://niceplace.test/pacbio/run');
    })
});

describe('Example fake remote api call', () => {
    const mockFetch = createFetchMock(vi);
    mockFetch.enableMocks();

    fetch.mockResolvedValue(
        new Promise( () => {
            stuff: 'nonsense'
        })
    );

    let client = new LangQc('https://niceplace.test');
    let response = client.getInboxPromise();
    // No internet used!
    test('Data in comes straight out again', () => {
        expect(response).resolves.toBe({
            stuff: 'nonsense'
        });

        expect(fetch.mock.calls.length).toEqual(1);
    });
});
