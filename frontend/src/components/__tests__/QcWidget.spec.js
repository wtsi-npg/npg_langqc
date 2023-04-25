import { describe, expect, test, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import { createTestingPinia } from '@pinia/testing';
import ElementPlus from 'element-plus';

import QcWidget from '@/components/QcWidget.vue';

describe('QC widgets render with no prior QC state, i.e. pending/ready', () => {
    const wrapper = mount(QcWidget, {
        global: {
            plugins: [ElementPlus, createTestingPinia({
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
                stubActions: false
            })],
            provide: {
                config: ref({
                    qc_states: [
                        { description: "Passed", only_prelim: false },
                        { description: "Failed", only_prelim: false },
                        { description: "On hold", only_prelim: true }
                    ]
                }),
            }
        },
    });
    /* RANT MODE ON
    vue3 recommends vitest with vue-test-utils (and not testing-library)
    but Element Plus components do not necessarily render correctly when
    mounted; the el-select generates an out-of-band div block that contains the
    pretty dropdown options that is outside of what is created by mount().
    In order to test Element Plus selector properly, we need to use
    testing-library/vue to render() the component. Then we lose easy access
    to the element attributes for things like disabled=""
    */

    test('No prior state results in message', () => {
        let div = wrapper.find('[data-testid="notHere"]');
        expect(div.text()).toEqual('No QC setting');
    });

    // TODO: Find a way to test the options in the dropdown are present
    // The el-select elements live somewhere funny in their own top-level
    // div.
    test('Status dropdown is populated and disabled', () => {
        // console.log(wrapper.html());
        let dropdown = wrapper.findAll('[placeholder="Select"]').at(0);
        expect(dropdown).toBeDefined();
        // TODO test this element is disabled when no state is assigned
        expect(dropdown.attributes('disabled')).toBe("");

        // Hacky way to find the generated el-select values
        // that only works when using testing-library/vue
        // vue-test-utils.mount() does not properly create the
        // el-select content divs
        // let choices = wrapper.findAll('.el-select-dropdown__item');
        // expect(choices).toHaveLength(3);
        // for(const [element, value] of _.zip(choices, expectedValues)) {
        //     console.log(element);
        //     console.log(value);
        //     expect(element.text()).toEqual(value);
        // }
    });

    test('Radio button defaults to preliminary', () => {
        let button = wrapper.get('[role=switch]');
        expect(button.attributes('aria-checked')).toEqual('false');
        expect(button.attributes('aria-disabled')).toEqual('true');
    });

    test('Radio button is disabled', () => {
        let button = wrapper.get('[role=switch]');
        expect(button.attributes('disabled')).toBe("");
    });

    test('Submit button is disabled', () => {
        let button = wrapper.get('button');
        expect(button.attributes('disabled')).toBe("");
    });

    test('Disable via prop turns off all controls', async () => {
        await wrapper.setProps({
            'componentDisabled': true
        });

        expect(wrapper.get('[role=switch]').attributes('disabled')).toEqual('');
        expect(wrapper.get('button').attributes('disabled')).toEqual('');
        expect(wrapper.get('[placeholder="Select"]').attributes('disabled')).toEqual('');
    });
});

describe('QC widget acquires state from prior outcome in run-table', () => {
    const wrapper = mount(QcWidget, {
        global: {
            plugins: [ElementPlus, createTestingPinia({
                createSpy: vi.fn,
                initialState: {
                    focusWell: {
                        runWell: {
                            run_info: {
                                pac_bio_run_name: 'TEST',
                                well_label: 'A1',
                            },
                            qc_state: {
                                qc_state: 'Claimed',
                                is_preliminary: true,
                                user: 'user@test.com'
                            },
                        },
                    },
                },
                stubActions: false
            })],
            provide: {
                config: ref({
                    qc_states: [
                        { description: "Passed", only_prelim: false },
                        { description: "Failed", only_prelim: false },
                        { description: "On hold", only_prelim: true }
                    ]
                }),
            }
        },
    });

    test('Message shown of previous state', () => {
        let div = wrapper.get('[data-testid="previousSetting"]');
        expect(div.text()).toEqual('Current QC state: Preliminary "Claimed" set by "user@test.com"');
    });

    test('Selector is preset to Claimed and active', () => {
        let dropdown = wrapper.findAll('[placeholder="Claimed"]').at(0);
        expect(dropdown).toBeDefined();

        expect(dropdown.attributes('disabled')).toBeUndefined();
    });

    test('Submit is not disabled', () => {
        expect(wrapper.get('[data-testid="QC submit"]').attributes('disabled')).toBeUndefined();
    });
});