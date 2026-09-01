import { test, expect } from 'vitest'
import { shortTxn } from './utils'

test('shortTxn correctly formats UUIDs and preserves DEMO IDs', () => {
  // Typical UUIDs should be truncated to 16 characters
  const longUuid = '123e4567-e89b-12d3-a456-426614174000'
  expect(shortTxn(longUuid)).toBe('123E4567-E89B-12')
  
  // Demo IDs under 24 chars should be fully preserved
  expect(shortTxn('DEMO_TXN_STRONG_1')).toBe('DEMO_TXN_STRONG_1')
  expect(shortTxn('DEMO_TXN_WEAK_2')).toBe('DEMO_TXN_WEAK_2')
  expect(shortTxn('DEMO_TXN_EMPTY_1')).toBe('DEMO_TXN_EMPTY_1')
  expect(shortTxn('DEMO_TXN_REVIEW_1')).toBe('DEMO_TXN_REVIEW_1')
})
