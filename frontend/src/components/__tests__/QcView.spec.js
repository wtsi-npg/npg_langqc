import { describe, expect, test, vi } from 'vitest';
import { render } from '@testing-library/vue';
// Pinia and ElementPlus required by ClaimWidget
import { createTestingPinia } from '@pinia/testing';
import ElementPlus from 'element-plus';

import QcView from '../QcView.vue';

describe('Component renders', () => {
  vi.stubEnv('VITE_SMRTLINK_PORT', '5555')
  vi.stubEnv('VITE_LIMS_SS_SERVER_URL', 'https://mylims.com')
  test('Good data', () => {
    const wrapper = render(QcView, {
      props: {
        runWell: {
          run_name: 'Test run',
          label: 'A1',
          well_complete_time: '19700101T000000',
          experiment_tracking: {
            study_id: ['1234'],
            study_name: 'My study',
            sample_id: '3456',
            sample_name: 'oldSock',
            num_samples: 1,
            library_type:['Pacbio_HiFi']
          },
          metrics: {
            smrt_link: {hostname: 'test.url', run_uuid: '123456'},
            metric1: {value: 9000, label: 'metric_one'},
            metric2: {value: 'VeryBad', label: 'metric_two'}
          }
        }
      },
      global: {
        plugins: [ElementPlus, createTestingPinia({ createSpy: vi.fn})],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    let link = wrapper.getByText("View in SMRT® Link");
    expect(link.getAttribute('href')).toBe('https://test.url:5555/sl/run-qc/123456');

    link = wrapper.getByText(/my study/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://mylims.com/studies/1234/properties');

    link = wrapper.getByText(/oldsock/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://mylims.com/samples/3456');
  });

});
