import { describe, expect, test, vi } from 'vitest';
import { render } from '@testing-library/vue';
// Pinia and ElementPlus required by ClaimWidget
import { createTestingPinia } from '@pinia/testing';
import ElementPlus from 'element-plus';

import QcView from '../QcView.vue';

describe('Component renders', () => {
  test('Good data', () => {
    const wrapper = render(QcView, {
      props: {
        runWell: {
          run_info: {
            pac_bio_run_name: 'Test run',
            well: {
              label: 'A1'
            },
            last_updated: '19700101T000000'
          },
          study: {
            id: 'Yay'
          },
          sample: {
            id: 'oldSock'
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

    const smrtlink = wrapper.getByText("View in SMRT® Link");

    expect(smrtlink.getAttribute('href')).toBe('https://test.url:8243/sl/run-qc/123456');
  });

});
