import { describe, test, expect } from 'vitest'

import { generateUrl, qcQueryChanged } from '../url'

describe('Test query setting in URL', () => {
  test('Set nothing, change nothing', () => {
    expect(
      generateUrl({
        option: '1'
      }, {},
      '/')
    ).toBeUndefined()
  })

  test('Set an option when there are none', () => {
    expect(
      generateUrl({}, {option: '1'}, '/')
    ).toEqual({
      path: '/',
      query: {
        option: '1'
      }
    })
  })

  test('Set an option redundantly changing nothing', () => {
    expect(
      generateUrl({option: '1'}, {option: '1'}, '/')
    ).toBeUndefined()
  })

  test('Override a previous setting', () => {
    expect(
      generateUrl({option: '1'}, {option: '2'}, '/')
    ).toEqual({
      path: '/',
      query: {
        option: '2'
      }
    })
  })

  test('Set several options including an override', () => {
    expect(
      generateUrl({option: '1'}, {option: '2', newOption: '1'}, '/')
    ).toEqual({
      path: '/',
      query: {
        option: '2',
        newOption: '1'
      }
    })
  })

  test('Unset an option', () => {
    expect(
      generateUrl({option: '1'}, {option: null}, '/')
    ).toEqual({
      path: '/',
      query: {}
    })
  })
})

describe('Test QC param check', () => {
  const testRun = {qcRun: 'test-run', qcLabel: 'A1'}
  const alteredTestRun = {qcRun: 'test-run', qcLabel: 'B1'}

  test('No before, some after', () => {
    expect(qcQueryChanged(undefined, testRun)).toBe(true)
  })

  test('None before, empty query after', () => {
    expect(qcQueryChanged(undefined, {})).toBe(false)
  })

  test('Some query before, none after', () => {
    expect(qcQueryChanged(testRun, {})).toBe(true)
  })

  test('Change of data from before to after', () => {
    expect(qcQueryChanged(testRun, alteredTestRun)).toBe(true)
  })
})