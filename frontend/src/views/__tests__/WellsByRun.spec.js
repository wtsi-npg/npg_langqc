import { describe, expect, test, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

import { createTestingPinia } from '@pinia/testing'
import ElementPlus from 'element-plus'
import { createRouter, createWebHistory } from 'vue-router'

import WellsByRun from '@/views/WellsByRun.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', redirect: '/ui/run' }, { path: '/ui/run', component: WellsByRun }]
})

const someLinkGeneration = {
  metrics: {
    smrt_link: {
      hostname: 'test.url',
      run_uuid: '123456',
      dataset_uuid: '789100'
    },
  },
  qc_state: null,
}

const testWells = []
for (let index = 0; index < 2; index++) {
  testWells.push({
    label: String.fromCharCode(97 + index) + "1",
    run_name: "TRACTION-RUN-211",
    run_start_time: "2023-04-24T10:10:10",
    run_complete_time: "2023-05-25T02:10:10",
    well_start_time: "2023-04-24T10:10:10",
    well_complete_time: "2023-05-25T02:10:10",
    run_status: "Complete",
    well_status: "Complete",
    instrument_name: "1234",
    instrument_type: "Revio",
    id_product: `${index}23456`,
    study_names: [`Study ${index}`, 'Another study'],
    ...someLinkGeneration
  })
}

const secondaryRun = {
  run_name: 'TRACTION-RUN-210',
  label: 'B1',
  instrument_name: '1234',
  instrument_type: 'Revio',
  id_product: 'ABCDEF',
  study_names: [],
  ...someLinkGeneration
}

const configResponse = {
  "qc_flow_statuses": [
    { "label": "Inbox", "param": "inbox" },
    { "label": "In Progress", "param": "in_progress" },
    { "label": "On Hold", "param": "on_hold" },
    { "label": "QC Complete", "param": "qc_complete" },
    { "label": "Aborted", "param": "aborted" },
    { "label": "Unknown", "param": "unknown" }
  ],
  "qc_states": [
    { "description": "Passed", "only_prelim": false },
    { "description": "Failed", "only_prelim": false },
    { "description": "Failed, Instrument", "only_prelim": false },
    { "description": "Failed, SMRT cell", "only_prelim": false },
    { "description": "On hold", "only_prelim": true },
    { "description": "Undecided", "only_prelim": false }
  ]
}

fetch.mockResponses(
  [
    // Contact the Okta API
    JSON.stringify({
      userinfo: {
        sub: "00ucz5ud94VnrDGv0416",
        email: "user@test.com",
        email_verified: true
      }
    }),
    { status: 200 }
  ],
  // watch() acts before onMount()
  // Get wells data
  [
    JSON.stringify({
      page_size: 100,
      page_number: 1,
      total_number_of_items: 2,
      wells: testWells
    }),
    { status: 200 }
  ],
)

function renderWellsByRun(props) {
  return mount(WellsByRun, {
    global: {
      plugins: [
        ElementPlus,
        createTestingPinia({
          createSpy: vi.fn,
          stubActions: false
        }),
        router
      ],
    },
    provide: {
      appConfig: ref(configResponse)
    },
    props: {
      runName: props
    }
  })
}

describe('Does it work?', async () => {
  let wrapper = renderWellsByRun(['TRACTION-RUN-211'])
  await flushPromises()
  test('Check network requests went out', () => {
    expect(fetch.mock.calls[0][0]).toEqual('http://localhost:3000/login-redirect?info=json')
    expect(fetch.mock.calls[1][0]).toEqual('/api/pacbio/run/TRACTION-RUN-211?page_size=100&page=1')
    expect(fetch.mock.calls.length).toEqual(2)
  })

  test('Check table was rendered with some data', () => {
    const table = wrapper.get('table')
    expect(table.exists()).toBe(true)
    const rows = table.findAll('tr')
    expect(rows.length).toEqual(3)
  })

  test('Click a well selection, QC View appears (because URL alters)', async () => {
    // Not providing precisely the right data, but serves for the component
    fetch.mockResponses(
      [JSON.stringify(secondaryRun)], // well QC data loading
    )

    let buttons = wrapper.findAll('button')
    buttons[1].trigger('click')
    await flushPromises()
    expect(wrapper.get('#well_summary').exists()).toBe(true)
  })

  test('Change from one target run to two' , async () => {
    fetch.mockResponses(
      // Get wells for all runs as component reloads data
      [
        JSON.stringify({
          page_size: 100,
          page_number: 1,
          total_number_of_items: 2,
          wells: testWells
        }),
        { status: 200 }
      ],
      [
        JSON.stringify({
          page_size: 100,
          page_number: 1,
          total_number_of_items: 1,
          wells: [secondaryRun]
        }),
        { status: 200 }
      ],
    )
    await wrapper.setProps({runName: ['TRACTION-RUN-211', 'TRACTION-RUN-210']})
    await flushPromises()

    const table = wrapper.get('table')
    expect(table.exists()).toBe(true)

    expect(table.find("td#TRACTION-RUN-211").exists()).toBe(true)
    expect(table.find("td#TRACTION-RUN-210").exists()).toBe(true)

    const rows = table.findAll('tr')
    expect(rows.length).toEqual(4)
  })
})
