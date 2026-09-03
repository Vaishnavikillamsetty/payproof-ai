export interface ScenarioTemplate {
  id: string
  category: 'strong' | 'weak' | 'contradiction' | 'empty'
  categoryLabel: string
  merchantId: string
  disputeReason: string
  customerClaim: string
  amount: number
}

export const SCENARIOS: ScenarioTemplate[] = [
  {
    id: 'DEMO_SCN_01',
    category: 'strong',
    categoryLabel: 'STRONG EVIDENCE',
    merchantId: 'MERCH_10482',
    disputeReason: 'subscription not cancelled',
    customerClaim: 'I emailed them to cancel my subscription before the renewal date but was still charged.',
    amount: 299.99,
  },
  {
    id: 'DEMO_SCN_02',
    category: 'strong',
    categoryLabel: 'STRONG EVIDENCE',
    merchantId: 'MERCH_90111',
    disputeReason: 'unauthorized transaction',
    customerClaim: 'I never made this transaction. My card must have been stolen.',
    amount: 129.50,
  },
  {
    id: 'DEMO_SCN_03',
    category: 'strong',
    categoryLabel: 'STRONG EVIDENCE',
    merchantId: 'MERCH_50122',
    disputeReason: 'product not received',
    customerClaim: 'The tracking has not updated in two weeks. I want my money back.',
    amount: 599.00,
  },
  {
    id: 'DEMO_SCN_04',
    category: 'strong',
    categoryLabel: 'STRONG EVIDENCE',
    merchantId: 'MERCH_21931',
    disputeReason: 'duplicate charge',
    customerClaim: 'I was charged twice for the same order within 5 minutes.',
    amount: 45.00,
  },
  {
    id: 'DEMO_SCN_05',
    category: 'weak',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_30219',
    disputeReason: 'product not received',
    customerClaim: 'Package says delivered but nothing is at my door.',
    amount: 120.00,
  },
  {
    id: 'DEMO_SCN_06',
    category: 'weak',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_44011',
    disputeReason: 'product not as described',
    customerClaim: 'The color is totally different from the website pictures.',
    amount: 89.99,
  },
  {
    id: 'DEMO_SCN_07',
    category: 'weak',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_77610',
    disputeReason: 'unauthorized transaction',
    customerClaim: 'Do not recognize this charge.',
    amount: 25.00,
  },
  {
    id: 'DEMO_SCN_08',
    category: 'weak',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_88200',
    disputeReason: 'product not received',
    customerClaim: 'Never got my software license key in my email.',
    amount: 150.00,
  },
  {
    id: 'DEMO_SCN_09',
    category: 'contradiction',
    categoryLabel: 'CONTRADICTORY EVIDENCE',
    merchantId: 'MERCH_11902',
    disputeReason: 'product not received',
    customerClaim: 'I have not received the item.',
    amount: 200.00,
  },
  {
    id: 'DEMO_SCN_10',
    category: 'contradiction',
    categoryLabel: 'CONTRADICTORY EVIDENCE',
    merchantId: 'MERCH_23004',
    disputeReason: 'product not received',
    customerClaim: 'I live alone and definitely did not sign for this package.',
    amount: 850.00,
  },
  {
    id: 'DEMO_SCN_11',
    category: 'contradiction',
    categoryLabel: 'CONTRADICTORY EVIDENCE',
    merchantId: 'MERCH_34111',
    disputeReason: 'product not as described',
    customerClaim: 'The merchant promised a refund on chat but never sent it.',
    amount: 199.99,
  },
  {
    id: 'DEMO_SCN_12',
    category: 'contradiction',
    categoryLabel: 'CONTRADICTORY EVIDENCE',
    merchantId: 'MERCH_45222',
    disputeReason: 'unauthorized transaction',
    customerClaim: 'Someone hacked my account and made this huge purchase.',
    amount: 1100.00,
  },
  {
    id: 'DEMO_SCN_13',
    category: 'empty',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_56333',
    disputeReason: 'product not as described',
    customerClaim: 'This arrived completely broken into pieces.',
    amount: 45.00,
  },
  {
    id: 'DEMO_SCN_14',
    category: 'empty',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_67444',
    disputeReason: 'subscription not cancelled',
    customerClaim: 'Forgot to cancel trial.',
    amount: 14.99,
  },
  {
    id: 'DEMO_SCN_15',
    category: 'empty',
    categoryLabel: 'INSUFFICIENT EVIDENCE',
    merchantId: 'MERCH_78555',
    disputeReason: 'duplicate charge',
    customerClaim: 'Charged me again for no reason.',
    amount: 75.00,
  }
]

export function getNextScenario(): { scenario: ScenarioTemplate, index: number } {
  const currentIdxStr = localStorage.getItem('payproof_demo_idx') || '0'
  let idx = parseInt(currentIdxStr, 10)
  if (isNaN(idx) || idx < 0 || idx >= SCENARIOS.length) {
    idx = 0
  }
  
  const scenario = SCENARIOS[idx]
  
  // Increment and persist for next time
  const nextIdx = (idx + 1) % SCENARIOS.length
  localStorage.setItem('payproof_demo_idx', nextIdx.toString())
  
  return { scenario, index: idx + 1 }
}
