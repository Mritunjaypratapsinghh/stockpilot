'use client';
import { useState, useEffect } from 'react';
import { api } from '../../lib/api';
import { Zap } from 'lucide-react';

const fmt = n => n?.toLocaleString('en-IN') || '0';

const s = {
  banner: { background: 'linear-gradient(135deg, var(--accent), #8b5cf6)', borderRadius: 12, padding: 24, margin: '0 0 24px 0', color: '#fff' },
  bannerTitle: { display: 'flex', alignItems: 'center', gap: 8, fontSize: 20, fontWeight: 700, margin: '0 0 8px 0', padding: 0 },
  bannerDesc: { fontSize: 14, opacity: 0.9, margin: 0, padding: 0 },
  bannerStat: { display: 'inline-block', background: 'rgba(255,255,255,0.15)', borderRadius: 8, padding: 12, margin: '16px 0 0 0' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 24, margin: 0, padding: 0 },
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 24, margin: 0 },
  title: { fontSize: 16, fontWeight: 600, margin: '0 0 24px 0', padding: 0 },
  label: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 8px 0', padding: 0 },
  inputRow: { display: 'flex', alignItems: 'center', gap: 8, margin: 0, padding: 0 },
  input: { flex: 1, padding: '10px 12px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 14, color: 'var(--text-primary)' },
  inputSmall: { width: 70, padding: '6px 8px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 13, color: 'var(--text-primary)', textAlign: 'right' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 8px 0', padding: 0 },
  slider: { width: '100%', height: 6, margin: '8px 0', padding: 0, accentColor: 'var(--accent)' },
  section: { margin: '0 0 20px 0', padding: 0 },
  hint: { fontSize: 11, color: 'var(--text-muted)', margin: '4px 0 0 0', padding: 0 },
  emi: { background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: 16, margin: '20px 0 0 0' },
  emiLabel: { fontSize: 11, color: 'var(--accent)', margin: '0 0 4px 0', padding: 0 },
  emiValue: { fontSize: 28, fontWeight: 700, margin: 0, padding: 0 },
  strategies: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, margin: '0 0 16px 0', padding: 0 },
  stratCard: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 16, margin: 0 },
  stratTitle: { fontSize: 13, fontWeight: 500, margin: '0 0 8px 0', padding: 0 },
  stratValue: { fontSize: 24, fontWeight: 700, color: 'var(--accent)', margin: '0 0 4px 0', padding: 0 },
  stratLabel: { fontSize: 11, color: 'var(--text-muted)', margin: '0 0 12px 0', padding: 0, textTransform: 'uppercase' },
  stratSaved: { borderTop: '1px solid var(--border)', padding: '12px 0 0 0', margin: '12px 0 0 0' },
  comboCard: { background: 'linear-gradient(135deg, var(--accent), #8b5cf6)', borderRadius: 12, padding: 16, margin: 0, color: '#fff' },
};

export default function LoanAnalyzer() {
  const [principal, setPrincipal] = useState(5000000);
  const [rate, setRate] = useState(8.5);
  const [tenure, setTenure] = useState(25);
  const [stepup, setStepup] = useState(7.5);
  const [extraEmis, setExtraEmis] = useState(1);
  const [result, setResult] = useState(null);

  useEffect(() => {
    api(`/api/v1/calculators/loan-analyzer?principal=${principal}&interest_rate=${rate}&tenure_years=${tenure}&stepup_pct=${stepup}&extra_emis=${extraEmis}`)
      .then(setResult).catch(console.error);
  }, [principal, rate, tenure, stepup, extraEmis]);

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 0 }}>
      <div style={s.banner}>
        <div style={s.bannerTitle}>Smart Loan Repayment Analyzer <Zap style={{ width: 20, height: 20, margin: 0, padding: 0 }} /></div>
        <p style={s.bannerDesc}>Discover how small changes in your repayment strategy can save you <strong>Lakhs</strong> in interest and cut years off your home loan.</p>
        {result && (
          <div style={s.bannerStat}>
            <div style={{ fontSize: 11, opacity: 0.8 }}>YEAR 1 REALITY CHECK</div>
            <div style={{ fontSize: 16, fontWeight: 600 }}>Total Paid (Yr 1): ₹{fmt(result.standard_emi * 12)}</div>
          </div>
        )}
      </div>

      <div style={s.grid}>
        <div style={s.card}>
          <h2 style={s.title}>Loan Details</h2>
          
          <div style={s.section}>
            <label style={s.label}>Loan Amount</label>
            <div style={s.inputRow}>
              <span style={{ color: 'var(--text-muted)' }}>₹</span>
              <input type="number" value={principal} onChange={e => setPrincipal(+e.target.value)} style={s.input} />
            </div>
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={s.label}>Interest Rate (%)</span><input type="number" value={rate} onChange={e => setRate(+e.target.value)} step="0.1" style={s.inputSmall} /></div>
            <input type="range" min="5" max="15" step="0.1" value={rate} onChange={e => setRate(+e.target.value)} style={s.slider} />
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={s.label}>Tenure (Years)</span><input type="number" value={tenure} onChange={e => setTenure(+e.target.value)} style={s.inputSmall} /></div>
            <input type="range" min="5" max="30" value={tenure} onChange={e => setTenure(+e.target.value)} style={s.slider} />
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={{ ...s.label, color: 'var(--accent)' }}>Step-Up Annual Increase (%)</span><input type="number" value={stepup} onChange={e => setStepup(+e.target.value)} step="0.5" style={s.inputSmall} /></div>
            <input type="range" min="0" max="20" step="0.5" value={stepup} onChange={e => setStepup(+e.target.value)} style={s.slider} />
            <p style={s.hint}>Used for Method 2 & 3</p>
          </div>

          <div style={s.section}>
            <div style={s.row}><span style={{ ...s.label, color: 'var(--accent)' }}>Extra EMIs per Year</span><input type="number" value={extraEmis} onChange={e => setExtraEmis(+e.target.value)} style={s.inputSmall} /></div>
            <input type="range" min="0" max="4" value={extraEmis} onChange={e => setExtraEmis(+e.target.value)} style={s.slider} />
            <p style={s.hint}>Used for Method 1 & 3 (Default: 1 = 13th month pay)</p>
          </div>

          {result && (
            <div style={s.emi}>
              <div style={s.emiLabel}>Standard Monthly EMI</div>
              <div style={s.emiValue}>₹{fmt(result.standard_emi)}</div>
            </div>
          )}
        </div>

        <div>
          {result && (
            <>
              <div style={s.strategies}>
                <div style={s.stratCard}>
                  <div style={s.stratTitle}>1 Extra EMI/Yr</div>
                  <div style={s.stratValue}>{result.strategies.extra_emi.tenure_saved}</div>
                  <div style={s.stratLabel}>Tenure Saved</div>
                  <div style={s.stratSaved}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Interest Saved</div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: '#10b981' }}>₹{fmt(result.strategies.extra_emi.interest_saved)}</div>
                  </div>
                </div>

                <div style={s.stratCard}>
                  <div style={s.stratTitle}>Step-Up ({stepup}%)</div>
                  <div style={s.stratValue}>{result.strategies.stepup.tenure_saved}</div>
                  <div style={s.stratLabel}>Tenure Saved</div>
                  <div style={s.stratSaved}>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Interest Saved</div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: '#10b981' }}>₹{fmt(result.strategies.stepup.interest_saved)}</div>
                  </div>
                </div>

                <div style={s.comboCard}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 13, fontWeight: 500, margin: '0 0 8px 0' }}>Super Combo <Zap style={{ width: 14, height: 14, margin: 0, padding: 0 }} /></div>
                  <div style={{ fontSize: 24, fontWeight: 700, margin: '0 0 4px 0' }}>{result.strategies.combo.tenure_saved}</div>
                  <div style={{ fontSize: 11, opacity: 0.8, margin: '0 0 12px 0', textTransform: 'uppercase' }}>Tenure Saved</div>
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.2)', padding: '12px 0 0 0', margin: '12px 0 0 0' }}>
                    <div style={{ fontSize: 11, opacity: 0.8 }}>Interest Saved</div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>₹{fmt(result.strategies.combo.interest_saved)}</div>
                  </div>
                </div>
              </div>

              <div style={s.card}>
                <div style={{ fontSize: 13, fontWeight: 500, margin: '0 0 12px 0' }}>Loan Balance Curve</div>
                <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-muted)' }}>
                  <span>— Standard</span>
                  <span style={{ color: '#3b82f6' }}>— Extra EMI</span>
                  <span style={{ color: '#8b5cf6' }}>— Step-Up</span>
                  <span style={{ color: '#10b981' }}>— Combo</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', margin: '12px 0 0 0' }}>Based on standard schedule. Prepayments drastically improve this ratio.</p>
              </div>
            </>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: 'var(--text-muted)', margin: '16px 0 0 0' }}>
        <span style={{ width: 16, height: 16, borderRadius: '50%', background: 'rgba(99,102,241,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>✓</span>
        Verified Methodology: Reducing Balance Method (RBI Guidelines)
      </div>
    </div>
  );
}
