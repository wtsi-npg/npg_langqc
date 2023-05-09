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
            smrt_link: {
              hostname: 'test.url',
              run_uuid: '123456',
              dataset_uuid: '78910'
            },
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

    let link = wrapper.getByText(/Test run/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://test.url:5555/sl/run-qc/123456');
    expect(link.parentElement.nodeName).toBe('TD');

    link = wrapper.getByText(/A1/).parentElement;
    expect(link.getAttribute('href')).toBe(
        'https://test.url:5555/sl/data-management/dataset-detail/78910?type=ccsreads&show=analyses');
    expect(link.parentElement.nodeName).toBe('TD');
    
    link = wrapper.getByText(/my study/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://mylims.com/studies/1234/properties');

    link = wrapper.getByText(/oldsock/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://mylims.com/samples/3456');
  });

  test('No host name', () => {
    const wrapper = render(QcView, {
      props: {
        runWell: {
          run_name: 'Test run2',
          label: 'B1',
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
            smrt_link: {
              hostname: '',
              run_uuid: '123456',
              dataset_uuid: '78910'
            },
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

    let td = wrapper.getByText(/Test run2/i).parentElement.nodeName;
    expect(td).toBe('TR');

    td = wrapper.getByText(/B1/).parentElement.nodeName;
    expect(td).toBe('TR');
  });

  test('No uuids', () => {
    const wrapper = render(QcView, {
      props: {
        runWell: {
          run_name: 'Test run3',
          label: 'C1',
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
            smrt_link: {
              hostname: 'myhost',
              run_uuid: null,
              dataset_uuid: null
            },
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

    let td = wrapper.getByText(/Test run3/i).parentElement.nodeName;
    expect(td).toBe('TR');

    td = wrapper.getByText(/C1/).parentElement.nodeName;
    expect(td).toBe('TR');
  });

});

