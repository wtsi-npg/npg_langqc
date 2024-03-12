import { describe, test, expect } from 'vitest'
import { combineLabelWithPlate, listStudiesForTooltip } from '../text'

describe('Well label and plate display', () => {
  test('Print well label without plate number', () => {
    expect(combineLabelWithPlate('A1', undefined)).toEqual('A1')
    expect(combineLabelWithPlate('A1', null)).toEqual('A1')
  })

  test('Print well label that includes plate number', () => {
    expect(combineLabelWithPlate('A1', 1)).toEqual('1-A1')
  })
})

describe('Study names tooltip', () => {
  test('Display a warning in case of an empty study array', () => {
    expect(listStudiesForTooltip([])).toEqual('No study info')
  })

  test('Display a single study name for an array of one study', () => {
    expect(listStudiesForTooltip(['My single study'])).toEqual('My single study')
  })

  test('Display multiple lines for multiple studies', () => {
    expect(listStudiesForTooltip(['Study One', 'Study two', 'Study 3'])).toEqual(
      'Study One<br />Study two<br />Study 3')
  })
})
