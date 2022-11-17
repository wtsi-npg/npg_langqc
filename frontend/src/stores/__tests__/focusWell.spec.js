import { setActivePinia, createPinia } from 'pinia';
import { describe, expect, beforeEach, test } from "vitest";

import { useWellStore } from "../focusWell";

describe('Check the getters', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
    })

    test('Get run name name and well label', () => {
        const wellStore = useWellStore();

        expect(wellStore.getRunAndLabel).toStrictEqual([null, null]);

        wellStore.setFocusWell({
            run_info: {
                pac_bio_run_name: 'Whatever',
                well_label: 'A1'
            }
        });

        expect(wellStore.getRunAndLabel).toStrictEqual(['Whatever', 'A1']);
    });

    test('getQcState', () => {
        const wellStore = useWellStore();

        expect(wellStore.getQcState).toBeNull();

        wellStore.setFocusWell({
            run_info: {
                nothing: 'to',
                see: 'here'
            },
            qcState: {
                state: 'Pass'
            }
        });

        expect(wellStore.getQcState).toEqual('Pass');

        wellStore.updateWellQcState({state: 'Fail'});
        expect(wellStore.getQcState).toEqual('Fail');
    });
});