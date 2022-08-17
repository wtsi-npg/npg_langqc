import { describe, expect, test } from 'vitest';
import { render } from '@testing-library/vue';
// import { mount } from '@vue/test-utils';

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
            sl_hostname: 'test.url',
            sl_run_uuid: '123456',
            metric1: 9000,
            metric2: 'VeryBad'
          }
        }
      }
    });

    const smrtlink = wrapper.getByText("View in SMRT® Link");

    expect(smrtlink.getAttribute('href')).toBe('https://test.url:8243/sl/run-qc/123456');
  });

});
