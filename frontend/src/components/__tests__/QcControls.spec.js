import { ref } from 'vue';
import { describe, expect, test, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createTestingPinia } from '@pinia/testing';
import ElementPlus from 'element-plus';

import QcControls from '@/components/QcControls.vue';

function mountWithState(well) {
    // We cannot shallowMount the QcControls to make the tests simpler, because
    // that stops the rendering of element-plus elements and any nested
    // elements. These tests must therefore satisfy the requirements of all
    // collocated components
    return mount(QcControls, {
        global: {
            plugins: [ElementPlus, createTestingPinia({
                createSpy: vi.fn,
                initialState: {
                    focusWell: {
                        well: well
                    },
                },
                stubActions: false
            })],
        },
        provide: {
            appConfig: ref({
                qc_states: [
                    { description: "Passed", only_prelim: false },
                    { description: "Failed", only_prelim: false },
                    { description: "On hold", only_prelim: true }
                ]
            }),
        }
    })
}

describe('Controls on unclaimed well', () => {
    const wrapper = mountWithState({
        run_info: {
            pac_bio_run_name: 'TEST',
            well_label: 'A1',
        },
    });

    test('No state, no user, no override', () => {
        expect(wrapper.find('button[id="override"]').exists()).toBe(false);
    });

    test('And now logged in, still no override for unclaimed', async () => {
        await wrapper.setProps({ 'user': 'dude' });
        expect(wrapper.find('button[id="override"]').exists()).toBe(false);
    });
});

describe('Controls for a claimed well', () => {
    const wrapper = mountWithState(
        {
            run_info: {
                pac_bio_run_name: 'TEST',
                well_label: 'A1',
            },
            qc_state: {
                qc_state: 'Claimed',
                is_preliminary: true,
                user: 'user@test.com'
            }
        });

    test('Not logged in, no override', () => {
        expect(wrapper.find('button[id="override"]').exists()).toBe(false);
    });

    test('Logged in, not the same user - can override', async () => {
        await wrapper.setProps({ 'user': 'dude' });
        expect(wrapper.find('button[id="override"]').exists()).toBe(true);
    });

    test('Logged in as correct user, no override for in-progress QC', async () => {
        await wrapper.setProps({ 'user': 'user@test.com' });
        expect(wrapper.find('button[id="override"]').exists()).toBe(false);
    });
});

describe('Controls for a finalised well', () => {
    const wrapper = mountWithState(
        {
            run_info: {
                pac_bio_run_name: 'TEST',
                well_label: 'A1',
            },
            qc_state: {
                qc_state: 'Passed',
                is_preliminary: false,
                user: 'user@test.com'
            }
        });

    test('Not logged in, no override', () => {
        expect(wrapper.find('button[id="override"]').exists()).toBe(false);
    });

    test('Other user, override available', async () => {
        await wrapper.setProps({ 'user': 'dude' });
        let overrideButton = wrapper.find('button[id="override"]')
        expect(overrideButton.exists()).toBe(true);
    });

    test('Correct user, override present to change from final', async () => {
        await wrapper.setProps({ 'user': 'user@test.com' });
        let overrideButton = wrapper.find('button[id="override"]')
        expect(overrideButton.exists()).toBe(true);
    });
});

describe('Check override function works correctly', () => {
    const wrapper = mountWithState(
        {
            run_info: {
                pac_bio_run_name: 'TEST',
                well_label: 'A1',
            },
            qc_state: {
                qc_state: 'Passed',
                is_preliminary: false,
                user: 'user@test.com'
            }
        });

    test('Override needed', async () => {
        expect(wrapper.get('[placeholder="Passed"]').attributes('disabled')).toEqual("");
        expect(wrapper.get('[data-testid="QC submit"]').attributes('disabled')).toEqual("");
    })


    test('Override disappears when clicked', async () => {
        await wrapper.setProps({ 'user': 'user@test.com' });
        await wrapper.find('button[id="override"').trigger('click');
        expect(wrapper.find('button[id="override"]').exists()).toBe(false);
    });

    test('Other widgets are enabled', () => {
        let button = wrapper.get('[role=switch]'); // The "Final" radio button
        expect(button.attributes('disabled')).toBeUndefined();

        expect(wrapper.get('[placeholder="Passed"]').attributes('disabled')).toBeUndefined(); // The state selector
        expect(wrapper.get('[data-testid="QC submit"]').attributes('disabled')).toBeUndefined(); // The submit button
    });
});
