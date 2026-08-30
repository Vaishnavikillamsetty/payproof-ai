import { useState } from 'react'
import { api } from '../api'

interface Props {
  onCancel: () => void
  onSuccess: (caseId: string) => void
}

export default function NewCase({ onCancel, onSuccess }: Props) {
  const [transactionId, setTransactionId] = useState('')
  const [merchantId, setMerchantId] = useState('')
  const [disputeReason, setDisputeReason] = useState('product not received')
  const [customerClaim, setCustomerClaim] = useState('')
  const [amountStr, setAmountStr] = useState('')
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (!transactionId || !merchantId || !customerClaim || !amountStr) {
      setError('Please fill out all fields.')
      return
    }

    const amount = parseFloat(amountStr)
    if (isNaN(amount) || amount <= 0) {
      setError('Amount must be a positive number.')
      return
    }

    setLoading(true)
    try {
      const newCase = await api.createCase({
        transaction_id: transactionId,
        merchant_id: merchantId,
        dispute_reason: disputeReason,
        customer_claim: customerClaim,
        amount: amount,
      })
      onSuccess(newCase.id)
    } catch (err: any) {
      setError(err.message || 'Failed to create case.')
      setLoading(false)
    }
  }

  const inputStyle = {
    width: '100%',
    background: 'var(--color-ink-light)',
    border: '1px solid var(--color-ink-border)',
    color: 'var(--color-white)',
    padding: '10px 14px',
    borderRadius: 6,
    fontFamily: 'var(--font-body)',
    fontSize: 15,
    outline: 'none',
  }

  const labelStyle = {
    display: 'block',
    fontFamily: 'var(--font-mono)',
    fontSize: 12,
    color: 'var(--color-slate)',
    marginBottom: 6,
    textTransform: 'uppercase' as const,
  }

  return (
    <main style={{ maxWidth: 600, margin: '60px auto', padding: '0 24px' }}>
      <h1 className="font-body" style={{ fontSize: 28, color: 'var(--color-white)', marginBottom: 32, fontWeight: 600 }}>
        New Dispute Case
      </h1>
      
      {error && (
        <div style={{ background: 'rgba(214, 72, 60, 0.1)', border: '1px solid var(--color-red)', padding: 16, borderRadius: 6, marginBottom: 24, color: 'var(--color-red)', fontFamily: 'var(--font-body)' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card" style={{ padding: 32, display: 'flex', flexDirection: 'column', gap: 24 }}>
        
        <div>
          <label style={labelStyle}>Transaction ID</label>
          <input 
            type="text" 
            value={transactionId} 
            onChange={e => setTransactionId(e.target.value)} 
            placeholder="e.g. TXN_123456789"
            style={inputStyle} 
          />
        </div>

        <div>
          <label style={labelStyle}>Merchant ID</label>
          <input 
            type="text" 
            value={merchantId} 
            onChange={e => setMerchantId(e.target.value)} 
            placeholder="e.g. MERCH_999"
            style={inputStyle} 
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          <div>
            <label style={labelStyle}>Dispute Reason</label>
            <select 
              value={disputeReason} 
              onChange={e => setDisputeReason(e.target.value)} 
              style={{ ...inputStyle, appearance: 'none', cursor: 'pointer' }}
            >
              <option value="product not received">Product Not Received</option>
              <option value="product not as described">Product Not As Described</option>
              <option value="duplicate charge">Duplicate Charge</option>
              <option value="subscription not cancelled">Subscription Not Cancelled</option>
              <option value="unauthorized transaction">Unauthorized Transaction</option>
            </select>
          </div>
          <div>
            <label style={labelStyle}>Amount ($)</label>
            <input 
              type="number" 
              step="0.01"
              value={amountStr} 
              onChange={e => setAmountStr(e.target.value)} 
              placeholder="e.g. 49.99"
              style={inputStyle} 
            />
          </div>
        </div>

        <div>
          <label style={labelStyle}>Customer Claim (Raw Text)</label>
          <textarea 
            value={customerClaim} 
            onChange={e => setCustomerClaim(e.target.value)} 
            placeholder="Enter the customer's exact explanation for the dispute..."
            rows={4}
            style={{ ...inputStyle, resize: 'vertical' }} 
          />
        </div>

        <div style={{ marginTop: 8, padding: '16px 20px', background: 'var(--color-ink-light)', borderRadius: 6, borderLeft: '4px solid var(--color-teal)' }}>
          <p className="font-body text-slate-light" style={{ fontSize: 13, margin: 0, lineHeight: 1.5 }}>
            Case submission starts the investigation. Evidence (payment records, OTP, delivery confirmation, merchant communication) is then retrieved and verified — the system does not just trust the claim as written.
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 16, marginTop: 16 }}>
          <button 
            type="button" 
            onClick={onCancel}
            disabled={loading}
            style={{ 
              background: 'transparent', border: '1px solid var(--color-ink-border)', 
              color: 'var(--color-slate)', padding: '10px 20px', borderRadius: 6, 
              cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-mono)', fontSize: 13, textTransform: 'uppercase'
            }}
          >
            Cancel
          </button>
          <button 
            type="submit" 
            disabled={loading}
            style={{ 
              background: 'var(--color-teal)', border: 'none', 
              color: '#000', padding: '10px 24px', borderRadius: 6, 
              cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, textTransform: 'uppercase',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Submitting...' : 'Create Case'}
          </button>
        </div>

      </form>
    </main>
  )
}
