import { describe, it, expect } from 'vitest'
import { isValidAiRecommendation, isPendingHumanDecision } from './components/SummaryStrip'
import type { Case } from './types'

describe('SummaryStrip KPI Logic', () => {
  describe('isValidAiRecommendation', () => {
    it('returns true for standard valid AI recommendations', () => {
      expect(isValidAiRecommendation('CONTEST')).toBe(true)
      expect(isValidAiRecommendation('APPROVE')).toBe(true)
      expect(isValidAiRecommendation('ACCEPT')).toBe(true)
      expect(isValidAiRecommendation('REQUEST_MORE_EVIDENCE')).toBe(true)
      expect(isValidAiRecommendation('ESCALATE')).toBe(true)
      expect(isValidAiRecommendation('STRONG_CASE')).toBe(true)
      expect(isValidAiRecommendation('WEAK_CASE')).toBe(true)
      expect(isValidAiRecommendation('HUMAN_REVIEW')).toBe(true)
      expect(isValidAiRecommendation('escalate')).toBe(true)
      expect(isValidAiRecommendation('request_more_evidence')).toBe(true)
    })

    it('returns false for null, undefined, empty, or error AI recommendations', () => {
      expect(isValidAiRecommendation(null)).toBe(false)
      expect(isValidAiRecommendation(undefined)).toBe(false)
      expect(isValidAiRecommendation('')).toBe(false)
      expect(isValidAiRecommendation('   ')).toBe(false)
      expect(isValidAiRecommendation('none')).toBe(false)
      expect(isValidAiRecommendation('NONE')).toBe(false)
      expect(isValidAiRecommendation('unknown')).toBe(false)
      expect(isValidAiRecommendation('FAILED')).toBe(false)
      expect(isValidAiRecommendation('ERROR')).toBe(false)
      expect(isValidAiRecommendation('AI_ANALYSIS_UNAVAILABLE')).toBe(false)
    })
  })

  describe('isPendingHumanDecision', () => {
    const baseCase: Case = {
      id: 'case-1',
      transaction_id: 'DEMO_1',
      dispute_reason: 'fraud',
      customer_claim: 'unauthorized',
      merchant_id: 'm_1',
      amount: 150,
      currency: 'USD',
      status: 'ESCALATED',
      ai_recommendation: 'ESCALATE',
      human_decision: null,
      contradiction_detected: false,
      completeness_score: 80,
      overall_confidence: 0.9,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      evidence_types: [],
      final_action: null,
    }

    it('returns true when valid AI recommendation exists and no human decision has been made', () => {
      expect(isPendingHumanDecision(baseCase)).toBe(true)
    })

    it('returns false if human decision already recorded', () => {
      const caseWithDecision = { ...baseCase, human_decision: 'CONTEST' }
      expect(isPendingHumanDecision(caseWithDecision)).toBe(false)

      const caseWithApprove = { ...baseCase, human_decision: 'APPROVE' }
      expect(isPendingHumanDecision(caseWithApprove)).toBe(false)
    })

    it('returns false if case is waiting for additional evidence', () => {
      const caseWaitingEvidence1 = { ...baseCase, status: 'evidence_requested' as const }
      expect(isPendingHumanDecision(caseWaitingEvidence1)).toBe(false)

      const caseWaitingEvidence2 = { ...baseCase, status: 'request_more_evidence' as const }
      expect(isPendingHumanDecision(caseWaitingEvidence2)).toBe(false)

      const caseWaitingEvidence3 = { ...baseCase, status: 'EVIDENCE_REQUESTED' as const }
      expect(isPendingHumanDecision(caseWaitingEvidence3)).toBe(false)
    })

    it('returns false if case is resolved or closed', () => {
      const caseResolved = { ...baseCase, status: 'resolved' as const }
      expect(isPendingHumanDecision(caseResolved)).toBe(false)

      const caseClosed = { ...baseCase, status: 'closed' as const }
      expect(isPendingHumanDecision(caseClosed)).toBe(false)

      const caseWon = { ...baseCase, status: 'won' as const }
      expect(isPendingHumanDecision(caseWon)).toBe(false)
    })

    it('returns false if AI recommendation is missing or failed', () => {
      const caseNoAi = { ...baseCase, ai_recommendation: null }
      expect(isPendingHumanDecision(caseNoAi)).toBe(false)

      const caseFailedAi = { ...baseCase, ai_recommendation: 'FAILED' }
      expect(isPendingHumanDecision(caseFailedAi)).toBe(false)
    })
  })

  describe('Evaluation on exact demo dataset', () => {
    const demoCases: Case[] = [
      {
        id: 'c1',
        transaction_id: 'DEMO_SCN_15_5T2S5O',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 250,
        currency: 'USD',
        status: 'ESCALATED',
        ai_recommendation: 'ESCALATE',
        human_decision: null,
        contradiction_detected: false,
        completeness_score: 90,
        overall_confidence: 0.85,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
      {
        id: 'c2',
        transaction_id: 'DEMO_SCN_14_SCQW5K',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 120,
        currency: 'USD',
        status: 'DECISION_RECORDED',
        ai_recommendation: 'ESCALATE',
        human_decision: 'CONTEST',
        contradiction_detected: false,
        completeness_score: 85,
        overall_confidence: 0.8,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
      {
        id: 'c3',
        transaction_id: 'DEMO_SCN_13_VXOJDA',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 300,
        currency: 'USD',
        status: 'evidence_requested',
        ai_recommendation: 'REQUEST_MORE_EVIDENCE',
        human_decision: 'REQUEST_MORE_EVIDENCE',
        contradiction_detected: false,
        completeness_score: 60,
        overall_confidence: 0.65,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
      {
        id: 'c4',
        transaction_id: 'DEMO_SCN_12_YA4ZPG',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 450,
        currency: 'USD',
        status: 'evidence_requested',
        ai_recommendation: 'REQUEST_MORE_EVIDENCE',
        human_decision: null,
        contradiction_detected: false,
        completeness_score: 55,
        overall_confidence: 0.6,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
      {
        id: 'c5',
        transaction_id: 'DEMO_SCN_10_RMQVVO',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 500,
        currency: 'USD',
        status: 'evidence_requested',
        ai_recommendation: 'REQUEST_MORE_EVIDENCE',
        human_decision: null,
        contradiction_detected: false,
        completeness_score: 50,
        overall_confidence: 0.55,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
      {
        id: 'c6',
        transaction_id: 'DEMO_SCN_09_JUT80E',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 180,
        currency: 'USD',
        status: 'escalated',
        ai_recommendation: 'ESCALATE',
        human_decision: 'REQUEST_MORE_EVIDENCE',
        contradiction_detected: false,
        completeness_score: 80,
        overall_confidence: 0.75,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
      {
        id: 'c7',
        transaction_id: 'DEMO_SCN_08_343ZDW',
        dispute_reason: 'fraud',
        customer_claim: 'claim',
        merchant_id: 'm1',
        amount: 90,
        currency: 'USD',
        status: 'resolved',
        ai_recommendation: 'REQUEST_MORE_EVIDENCE',
        human_decision: 'APPROVE',
        contradiction_detected: false,
        completeness_score: 80,
        overall_confidence: 0.75,
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
        evidence_types: [],
        final_action: null,
      },
    ]

    it('correctly counts 7 AI recommendations ready across all 7 cases', () => {
      const recommendationsReady = demoCases.filter(c => isValidAiRecommendation(c.ai_recommendation)).length
      expect(recommendationsReady).toBe(7)
    })

    it('correctly counts 1 pending human decision (DEMO_SCN_15_5T2S5O only)', () => {
      const pendingReview = demoCases.filter(isPendingHumanDecision).length
      expect(pendingReview).toBe(1)

      const pendingCases = demoCases.filter(isPendingHumanDecision)
      expect(pendingCases[0].transaction_id).toBe('DEMO_SCN_15_5T2S5O')
    })
  })
})
