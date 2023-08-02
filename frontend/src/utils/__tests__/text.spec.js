import { describe, test, expect } from 'vitest'
import combineLabelWithPlate from '../text'

describe('Text processing', () => {
  test('Print well label without plate number', () => {
    expect(combineLabelWithPlate('A1', undefined)).toEqual('A1')
    expect(combineLabelWithPlate('A1', null)).toEqual('A1')
  })

  test('Print well label that includes plate number', () => {
    expect(combineLabelWithPlate('A1', 1)).toEqual('1-A1')
  })
})
