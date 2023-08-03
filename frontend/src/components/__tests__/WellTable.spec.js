import { describe, expect, test } from 'vitest'
import { mount } from '@vue/test-utils'

import WellTable from '@/components/WellTable.vue'

describe('Rows of data give rows in the table', () => {
  const table = mount(WellTable, {
    props: {
      wellCollection: [
        {run_name: 'TEST1', label: 'A1', instrument_name: '1234', instrument_type: 'Revio', id_product: 'ABCDEF'},
        {run_name: 'TEST1', label: 'B1', instrument_name: '1234', instrument_type: 'Revio', id_product: '123456'},
      ]
    }
  })

  test('There are two rows plus a header in the table', () => {
    const rows = table.findAll('tr')
    expect(rows.length).toEqual(3)

    const columns = rows[1].findAll('td')
    expect(columns[0].text()).toEqual('TEST1')
    expect(columns[1].text()).toEqual('A1')
    expect(columns[2].text()).toEqual('Revio 1234')
    for (let col of columns.splice(3)) {
      expect(col.text()).toEqual('')
    }
  })

  test('Clicking triggers event emits containing required data', async () => {
    const rows = table.findAll('tr')
    await rows[1].find('button').trigger('click')

    expect(table.emitted().wellSelected[0][0]).toHaveProperty('idProduct')
    expect(table.emitted().wellSelected[0][0].idProduct).toEqual('ABCDEF')

    await rows[2].find('button').trigger('click')
    expect(table.emitted().wellSelected[1][0].idProduct).toEqual('123456')
  })
})