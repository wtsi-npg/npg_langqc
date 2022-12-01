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
                    },
                    qcState: null
                },
            },
            stubActions: false
            })],
            provide: {
                config: ref({
                    qc_states: [
                        {description: "Passed", only_prelim: false},
                        {description: "Failed", only_prelim: false},
                        {description: "On hold", only_prelim: true}
                    ]
                }),
                activeWell: ref({
                    runName: "TEST",
                    label: "A1"
                })
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

    test('Submit button is disabled', () => {
        let button = wrapper.get('button');
        expect(button.attributes('aria-disabled')).toEqual('true');
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
                        }
                    },
                    qcState: {
                        qc_state: 'Claimed',
                        is_preliminary: true,
                        user: 'user@test.com'
                    }
                },
            },
            stubActions: false
            })],
            provide: {
                config: ref({
                    qc_states: [
                        {description: "Passed", only_prelim: false},
                        {description: "Failed", only_prelim: false},
                        {description: "On hold", only_prelim: true}
                    ]
                }),
                activeWell: ref({
                    runName: "TEST",
                    label: "A1"
                })
            }
        },
    });

    test('Message shown of previous state', () => {
        let div = wrapper.get('[data-testid="previousSetting"]');
        expect(div.text()).toEqual('Current QC state: Preliminary "Claimed" set by "user@test.com"');
    });

    test('Selector is preset to Claimed', () => {
        let dropdown = wrapper.findAll('[placeholder="Claimed"]').at(0);
        expect(dropdown).toBeDefined();

        expect(dropdown.attributes('disabled')).toBeUndefined();
    });
});