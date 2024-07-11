import { describe, expect, test } from 'vitest'
import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'

import PoolStats from '../PoolStats.vue'

const wrapper = mount(PoolStats, {
    global: {
        plugins: [ElementPlus],
    },
    props: {
        pool: {
            pool_coeff_of_variance: 47.2,
            products: [{
                id_product: 'A'.repeat(64),
                tag1_name: 'TTTTTTTT',
                tag2_name: null,
                deplexing_barcode: 'bc10--bc10',
                hifi_read_bases: 900,
                hifi_num_reads: 20,
                hifi_read_length_mean: 45,
                hifi_bases_percent: 90.001,
                percentage_total_reads: 66.6
            },{
                id_product: 'B'.repeat(64),
                tag1_name: 'GGGGGGGG',
                tag2_name: null,
                deplexing_barcode: 'bc11--bc11',
                hifi_read_bases: 100,
                hifi_num_reads: 10,
                hifi_read_length_mean: 10,
                hifi_bases_percent: 100,
                percentage_total_reads: 33.3
            }]
        }
    }
})

describe('Create poolstats table with good data', () => {
    test('Component is "folded" by default', () => {
        expect(wrapper.getComponent('transition-stub').attributes()['appear']).toEqual('false')
    })

    test('Coefficient of variance showing', async () => {
        let topStat = wrapper.find('p')
        await topStat.trigger('focus')
        expect(topStat.classes('el-tooltip__trigger')).toBeTruthy()

        expect(topStat.text()).toEqual('Coefficient of Variance: 47.2')
    })

    test('Table looks about right', () => {
        let rows = wrapper.findAll('tr')
        expect(rows.length).toEqual(3)

        // Check tag 1 has been set
        expect(rows[1].find('td').text()).toEqual('TTTTTTTT')
        expect(rows[2].find('td').text()).toEqual('GGGGGGGG')
    })
})