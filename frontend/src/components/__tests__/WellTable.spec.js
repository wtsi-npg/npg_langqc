import { describe, expect, test } from 'vitest'
import { mount } from '@vue/test-utils'

import WellTable from '@/components/WellTable.vue'

describe('Rows of data give rows in the table', () => {
  const table = mount(WellTable, {
    props: {
      wellCollection: [
        {
          run_name: 'TEST1',
          label: 'A1',
          plate_number: null,
          instrument_name: '1234',
          instrument_type: 'Revio',
          id_product: 'ABCDEF',
          study_names: []
        },
        {
          run_name: 'TEST1',
          label: 'B1',
          plate_number: null,
          instrument_name: '1234',
          instrument_type: 'Revio',
          id_product: '123456',
          study_names: ['Study name 1', 'Study name 2']
        },
        {
          run_name: 'TEST2',
          label: 'A1',
          plate_number: 1,
          instrument_name: '1234',
          instrument_type: 'Revio',
          id_product: '123457',
          study_names: ['BIOSCAN UK for flying insects']
        },
      ]
    }
  })

  test('There are three rows plus a header in the table', () => {
    const rows = table.findAll('tr')
    expect(rows.length).toEqual(4)
    let columns = rows[1].findAll('td')
    expect(columns[0].text()).toEqual('TEST1')
    expect(columns[1].text()).toEqual('A1')
    expect(columns[2].text()).toEqual('Revio 1234')
    for (let col of columns.splice(3)) {
      expect(col.text()).toEqual('')
    }
    columns = rows[3].findAll('td')
    expect(columns[1].text()).toEqual('1-A1')
  })

  test('Non-null plate_number gives modified well labels', () => {
    const row = table.find('table tr:nth-of-type(4)')
    expect(row.find('td:nth-of-type(2)').text()).toEqual('1-A1')
  })

  test('Clicking triggers event emits containing required data', async () => {
    const rows = table.findAll('tr')
    await rows[1].find('button').trigger('click')

    expect(table.emitted().wellSelected[0][0]).toHaveProperty('idProduct')
    expect(table.emitted().wellSelected[0][0].idProduct).toEqual('ABCDEF')

    let wellButton = rows[2].find('button')
    await wellButton.trigger('click')
    expect(table.emitted().wellSelected[1][0].idProduct).toEqual('123456')
    expect(wellButton.classes('el-tooltip__trigger')).toBeTruthy()
    expect(wellButton.classes('el-button--info')).toBeTruthy()

    wellButton = rows[3].find('button')
    expect(wellButton.classes('el-tooltip__trigger')).toBeTruthy()
    expect(wellButton.classes('el-button--warning')).toBeTruthy()
  })
})
