import { beforeEach, describe, expect, test, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ElementPlus from 'element-plus';

import ClaimWidget from '../ClaimWidget.vue';
import { useWellStore } from '@/stores/focusWell.js';

describe('Clicking triggers POST and side-effects', () => {
    // A typical claim success
    fetch.mockResponse(
        JSON.stringify({
            id_product: 'ABCDEF',
            qc_state: 'Claimed',
            outcome: null,
            is_preliminary: true,
            qc_type: 'sequencing',
            date_updated: '20221019T090000Z',
            user: 'loggedInUser'
        })
    );
    let { widget, wellStore } = [null, null, null];

    // All subsequent tests expect the claim widget to be enabled
    beforeEach(() => {
        widget = mount(ClaimWidget, {
            global: {
                plugins: [
                    ElementPlus,
                    createTestingPinia({
                        createSpy: vi.fn,
                        initialState: {
                            focusWell: {
                                well: {
                                    id_product: 'ABCDEF',
                                    run_name: 'TEST',
                                    label: 'A1',
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
    });

    test('Click normally', async () => {
        expect(widget.get('button').attributes('disabled')).toBeUndefined()
        await widget.get('button').trigger('click');
        await flushPromises(); // Forces reactivity to shake out
        expect(wellStore.getQcValue).toEqual('Claimed');

        let request = fetch.mock.calls[0];
        expect(request[0]).toEqual('/api/pacbio/products/ABCDEF/qc_claim');

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
        // Notice ElMessage elements have appeared somehow?

        expect(widget.emits).not.toBeDefined();
    });
});

describe('Disablement works as desired', () => {
    test('Disabled', () => {
        let widget = mount(ClaimWidget, {
            global: {
                plugins: [
                    ElementPlus,
                    createTestingPinia({
                        createSpy: vi.fn,
                    })
                ],
            },
            props: {
                'disabled': true
            }
        })

        expect(widget.get('button').attributes('disabled')).toBeDefined()
    })
})