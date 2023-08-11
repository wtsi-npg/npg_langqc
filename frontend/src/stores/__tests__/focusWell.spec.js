import { setActivePinia, createPinia } from 'pinia';
import { describe, expect, beforeEach, test } from "vitest";

import { useWellStore } from "../focusWell";

describe('Check the getters', () => {
    let wellStore = null;
    beforeEach(() => {
        setActivePinia(createPinia())
        wellStore = useWellStore();
    })

    test('Get id_product', () => {
        expect(wellStore.getIdProduct).toBeNull()

        wellStore.setFocusWell({
            id_product: 'ABCDEF'
        })

        expect(wellStore.getIdProduct).toEqual('ABCDEF')
    })

    test('getQcState', () => {
        expect(wellStore.getQcState).toBeNull();

        wellStore.setFocusWell({
            nothing: 'to',
            see: 'here'
        });
        wellStore.updateWellQcState({
            qc_state: 'Pass',
            user: 'test'
        });

        expect(wellStore.hasQcState).toBe(true);
        expect(wellStore.getQcValue).toEqual('Pass');

        wellStore.updateWellQcState({ qc_state: 'Fail' });
        expect(wellStore.getQcValue).toEqual('Fail');
    });

    test('getFinality', () => {
        expect(wellStore.getFinality).toBeFalsy();

        wellStore.setFocusWell({
            run_name: 'Whatever',
            label: 'A1'
        });
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
