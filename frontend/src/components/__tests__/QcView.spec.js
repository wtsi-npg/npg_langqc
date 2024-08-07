import { describe, expect, test, vi, afterEach } from 'vitest';
import { render, cleanup } from '@testing-library/vue';
import ElementPlus from 'element-plus';

import QcView from '../QcView.vue';

describe('Component renders', () => {

  // Supply PoolStats element with some data
  fetch.mockResponse(
    JSON.stringify({})
  )

  afterEach(async () => {
    cleanup()
  });

  vi.stubEnv('VITE_SMRTLINK_PORT', '5555')
  vi.stubEnv('VITE_LIMS_SS_SERVER_URL', 'https://mylims.com')

  let experiment_init = {
    study_id: ['1234'],
    study_name: 'My study',
    sample_id: '3456',
    sample_name: 'oldSock',
    num_samples: 1,
    library_type:['Pacbio_HiFi'],
    pool_name: "TRAC-2-3456"
  };

  let props_1 = {
    well: {
      run_name: 'Test run',
      label: 'A1',
      plate_number: null,
      well_complete_time: '2021-01-17T08:35:18',
      experiment_tracking: experiment_init,
      metrics: {
        smrt_link: {
          hostname: 'test.url',
          run_uuid: '123456',
          dataset_uuid: '789100'
        },
        metric1: {value: 9000, label: 'metric_one'},
        metric2: {value: 'VeryBad', label: 'metric_two'}
      },
      instrument_name: '1234',
      instrument_type: 'Revio',
    }
  };

  test('Good data', () => {
    const wrapper = render(QcView, {
      props: props_1,
      global: {
        plugins: [ElementPlus],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    let link = wrapper.getByText(/Test run/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://test.url:5555/sl/run-qc/123456');
    link = wrapper.getByText(/A1/).parentElement;
    expect(link.getAttribute('href')).toBe(
      'https://test.url:5555/sl/data-management/dataset-detail/789100?type=ccsreads&show=analyses'
    );

    link = wrapper.getByText(/my study/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://mylims.com/studies/1234/properties');

    link = wrapper.getByText(/oldsock/i).parentElement;
    expect(link.getAttribute('href')).toBe('https://mylims.com/samples/3456');

    expect(wrapper.html()).toMatch(/17\/01\/2021|1\/17\/2021/) //American style dates in CI

    expect(wrapper.getByText('TRAC-2-3456')).toBeDefined()

    expect(wrapper.getByText('Revio 1234')).toBeDefined()
  });


  test('No LIMS data, no well complete date', () => {

    props_1['well']['experiment_tracking'] = null
    props_1['well']['well_complete_time'] = null
    const wrapper = render(QcView, {
      props: props_1,
      global: {
        plugins: [ElementPlus],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    let html = wrapper.html()
    let expected_text = [
      'No well completion timestamp',
      'No study information',
      'No sample information',
      'No library type information'
    ]
    expected_text.forEach((value) => {expect(html).toContain(value)});

  });

  test('Multiple LIMS entities', () => {

    let experiment = {
      study_id: ['1234', '1235'],
      study_name: null,
      sample_id: null,
      sample_name: null,
      num_samples: 4,
      library_type:['Pacbio_HiFi', 'PacBio_Standard']
    };
    props_1['well']['experiment_tracking'] = experiment

    const wrapper = render(QcView, {
      props: props_1,
      global: {
        plugins: [ElementPlus],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    let html = wrapper.html()
    let expected_text = [
      'Multiple studies: 1234, 1235',
      'Multiple samples (4)',
      'Pacbio_HiFi, PacBio_Standard'
    ]
    expected_text.forEach((value) => {expect(html).toContain(value)});

  });

  test('No host name for links to SmrtLink', () => {

    props_1['well']['metrics']['smrt_link'] = {
      hostname: null,
      run_uuid: '123456',
      dataset_uuid: '789100'
    };

    const wrapper = render(QcView, {
      props: props_1,
      global: {
        plugins: [ElementPlus],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    let tr = wrapper.getByText(/Test run/i).parentElement.nodeName;
    expect(tr).toBe('TR'); //parent is not a link
    tr = wrapper.getByText(/A1/).parentElement.nodeName;
    expect(tr).toBe('TR');

  });

  test('No UUIDs for links to SmrtLink', () => {

    props_1['well']['metrics']['smrt_link'] = {
      hostname: 'somehost',
      run_uuid: null,
      dataset_uuid: null
    };

    const wrapper = render(QcView, {
      props: props_1,
      global: {
        plugins: [ElementPlus],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    let tr = wrapper.getByText(/Test run/i).parentElement.nodeName;
    expect(tr).toBe('TR');
    tr = wrapper.getByText(/A1/).parentElement.nodeName;
    expect(tr).toBe('TR');

  });

});

describe('Numbered plates in runs also render ok', () => {
  let experiment_init = {
    study_id: ['1234'],
    study_name: 'My study',
    sample_id: '3456',
    sample_name: 'oldSock',
    num_samples: 1,
    library_type:['Pacbio_HiFi'],
    pool_name: "TRAC-2-3456"
  };

  let props_2 = {
    well: {
      run_name: 'Test run 2',
      label: 'A1',
      plate_number: '1',
      well_complete_time: '2021-01-17T08:35:18',
      experiment_tracking: experiment_init,
      metrics: {
        smrt_link: {
          hostname: 'test.url',
          run_uuid: '123456',
          dataset_uuid: '789100'
        },
        metric1: {value: 9000, label: 'metric_one'},
        metric2: {value: 'VeryBad', label: 'metric_two'}
      },
      instrument_name: '1234',
      instrument_type: 'Revio',
    }
  };

  test('Numbered plate is combined into the "well label"', () => {
    const wrapper = render(QcView, {
      props: props_2,
      global: {
        plugins: [ElementPlus],
        provide: {
          activeTab: 'inbox'
        }
      }
    });

    expect(wrapper.html()).toContain('1-A1');
  });
});