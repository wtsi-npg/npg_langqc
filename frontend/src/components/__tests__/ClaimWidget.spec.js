import { beforeEach, describe, expect, test, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ElementPlus from 'element-plus';

import ClaimWidget from '../ClaimWidget.vue';
import { useWellStore } from '@/stores/focusWell.js';
import { useMessageStore } from '@/stores/message.js';

describe('Clicking triggers POST and side-effects', () => {
    // A typical claim success
    fetch.mockResponse(
        JSON.stringify({
            state: 'Claimed',
            outcome: null,
            is_preliminary: true,
            qc_type: 'sequencing',
            date_updated: '20221019T090000Z',
            user: 'loggedInUser'
        })
    );
    let { widget, wellStore, messageStore }  = [null, null, null];

    beforeEach(() => {
        widget = mount(ClaimWidget, {
            global: {
                plugins: [
                    ElementPlus,
                    createTestingPinia({
                        createSpy: vi.fn,
                        initialState: {
                            focusWell: {
                                runWell: {
                                    run_info: {
                                        pac_bio_run_name: 'TEST',
                                        well_label: 'A1',
                                    }
                                }
                            },
                        },
                        // This is the important bit!
                        // PiniaTesting doesn't run actual code by default
                        stubActions: false
                    })
                ],
                provide: {
                    activeTab: 'inbox'
                }
            }
        });
        wellStore = useWellStore();
        messageStore = useMessageStore();
    });



    test('Click normally', async () => {
        await widget.get('button').trigger('click');
        await flushPromises(); // Forces reactivity to shake out

        expect(messageStore.errorMessages).toHaveLength(0);
        expect(wellStore.getQcState).toEqual('Claimed');

        let request = fetch.mock.calls[0];
        expect(request[0]).toEqual('/api/pacbio/run/TEST/well/A1/qc_claim');

        let emits = widget.emitted();
        expect(emits.wellClaimed).toBeTruthy();

        // Click again - should do nothing
        await widget.get('button').trigger('click');
        expect(widget.emitted().wellClaimed).toStrictEqual(emits.wellClaimed);
    });

    test('Click with a failed API call', async () => {
        fetch.mockRejectOnce('API says no');

        await widget.get('button').trigger('click');
        await flushPromises();
        expect(messageStore.errorMessages).toHaveLength(1);
        expect(messageStore.errorMessages).toEqual(["API says no"]);

        expect(widget.emits).not.toBeDefined();
    });
});
