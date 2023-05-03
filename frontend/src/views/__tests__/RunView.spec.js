import { describe, expect, test, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils';
// import {createRouter, createWebHistory} from 'vue-router'
// or routes arg to render(Component, {routes: []|vue-router obj})

import { createTestingPinia } from '@pinia/testing'
import ElementPlus from 'element-plus'
import { createRouter, createWebHistory } from 'vue-router';

import RunView from '@/views/RunView.vue'

// The giga-faking of most of the app:


const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', redirect: '/ui/wells' }, { path: '/ui/wells', component: RunView }]
})

const testWells = []
for (let index = 0; index < 10; index++) {
  testWells.push({
    label: String.fromCharCode(94 + index) + "1",
    run_name: `TRACTION-RUN-21${(index / 10).toFixed(0)}`,
    run_start_time: "2023-04-24T10:10:10",
    run_complete_time: "2023-05-25T02:10:10",
    well_start_time: "2023-04-24T10:10:10",
    well_complete_time: "2023-05-25T02:10:10",
    run_status: "Complete",
    well_status: "Complete",
    qc_state: null
  })
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
  [
    // Load client config from API
    JSON.stringify(configResponse),
    { status: 200 }
  ],
  // Get wells data
  [
    JSON.stringify({
      page_size: 10,
      page_number: 1,
      total_number_of_items: 100,
      qc_flow_status: "inbox",
      wells: testWells
    }),
    { status: 200 }
  ],
)

const wrapper = mount(RunView, {
  global: {
    plugins: [
      ElementPlus,
      createTestingPinia({
        createSpy: vi.fn,
        stubActions: false
      }),
      router
    ],
  }
})



describe('View loads configuration on mount', async () => {
  // onMount populates a Pinia store. Wait for reactivity to occur
  await flushPromises()

  test('Tabs in run-table configured and rendered', () => {
    for (const flowStatus of configResponse.qc_flow_statuses) {
      let tabId = `[id="tab-${flowStatus['param']}"]`
      expect(wrapper.find(tabId).exists()).toBe(true)
    }
  })

  test('Default tab is inbox', () => {
    const inboxButton = wrapper.get('[id="tab-inbox"]')
    expect(inboxButton.classes('is-active')).toBeTruthy()
  })

  test('Runs are rendered in rows', () => {
    const table = wrapper.get('table')
    expect(table.exists()).toBe(true)
    const rows = table.findAll('tr')
    expect(rows.length).toEqual(11) // 10 rows plus header
  })

  test('Navigating to another tab makes things happen', async () => {
    // Anticipate the loading of new tab data
    fetch.mockResponseOnce(
      JSON.stringify({
        page_size: 10,
        page_number: 1,
        total_number_of_items: 1,
        qc_flow_status: "on_hold",
        wells: [{
          label: 'X1',
          run_name: 'TRACTION-RUN-299',
          run_start_time: "2023-04-24T10:10:10",
          run_complete_time: "2023-05-25T02:10:10",
          well_start_time: "2023-04-24T10:10:10",
          well_complete_time: "2023-05-25T02:10:10",
          run_status: "Complete",
          well_status: "Complete",
          qc_state: null
        }]
      })
    )

    await wrapper.get('[id="tab-on_hold"]').trigger('click')
    await flushPromises() // Awaiting data change, but also router.isReady

    expect(fetch.requests().slice(-1)[0].url).toEqual('/api/pacbio/wells?qc_status=on_hold&page_size=10&page_number=1')
    // Access the current route by strange fashion
    expect(router.currentRoute.value.query).toEqual({activeTab: 'on_hold', page: '1'})
  })
})
