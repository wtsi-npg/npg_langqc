import { setActivePinia, createPinia } from 'pinia';
import { describe, expect, beforeEach, test } from "vitest";

import { useWellStore } from "../focusWell";

describe('Check the getters', () => {
    let wellStore = null;
    beforeEach(() => {
        setActivePinia(createPinia())
        wellStore = useWellStore();
    })

    test('Get run name name and well label', () => {
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
        expect(wellStore.getQcState).toBeNull();

        wellStore.setFocusWell({
            run_info: {
                nothing: 'to',
                see: 'here'
            }
        });
        wellStore.updateWellQcState({
            qc_state: 'Pass',
            user: 'test'
        });

        expect(wellStore.hasQcState).toBe(true);
        expect(wellStore.getQcValue).toEqual('Pass');

        wellStore.updateWellQcState({qc_state: 'Fail'});
        expect(wellStore.getQcValue).toEqual('Fail');
    });

    test('getFinality', () => {
        expect(wellStore.getFinality).toEqual(null);

        wellStore.updateWellQcState({
            qc_state: 'Pass',
            user: 'test',
            is_preliminary: true
        });

        expect(wellStore.getFinality).toBe(false);

        wellStore.updateWellQcState({
            qc_state: 'Pass',
            user: 'test',
            is_preliminary: false
        });

        expect(wellStore.getFinality).toBe(true);
    });
});