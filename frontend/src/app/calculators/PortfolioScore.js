'use client';
import { useState } from 'react';
import { api } from '../../lib/api';
import { ChevronRight } from 'lucide-react';

const questions = [
  { q: "How well do you know your current Equity vs. Debt allocation?", opts: ["I know the exact ratio (e.g., 60:40)", "I have a rough estimate", "I don't actively track it", "I have never checked"] },
  { q: "How diversified is your portfolio across asset classes?", opts: ["Very diversified (5+ asset classes)", "Moderately diversified (3-4)", "Somewhat diversified (2)", "Not diversified (1)"] },
  { q: "Do you have an emergency fund?", opts: ["Yes, 6+ months expenses", "Yes, 3-6 months", "Yes, less than 3 months", "No emergency fund"] },
  { q: "How regularly do you invest?", opts: ["Monthly SIP/automatic", "Quarterly", "Occasionally", "Rarely/Never"] },
  { q: "Are your investments aligned with specific goals?", opts: ["Yes, all mapped to goals", "Most are goal-based", "Some are goal-based", "No specific goals"] },
  { q: "How often do you review your portfolio?", opts: ["Monthly", "Quarterly", "Yearly", "Never"] },
];

const s = {
  card: { background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 12, padding: 32, margin: '0 auto', maxWidth: 600 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: '0 0 32px 0', padding: 0 },
  title: { fontSize: 18, fontWeight: 600, margin: 0, padding: 0 },
  step: { fontSize: 13, color: 'var(--text-muted)', margin: 0, padding: 0 },
  progress: { width: '100%', height: 4, background: 'var(--bg-tertiary)', borderRadius: 2, margin: '0 0 32px 0', padding: 0 },
  progressBar: { height: 4, background: 'var(--accent)', borderRadius: 2, transition: 'width 0.3s' },
  question: { fontSize: 20, fontWeight: 500, textAlign: 'center', margin: '0 0 32px 0', padding: 0 },
  options: { display: 'flex', flexDirection: 'column', gap: 12, margin: 0, padding: 0 },
  optBtn: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', margin: 0, background: 'var(--bg-tertiary)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 14, textAlign: 'left', cursor: 'pointer', transition: 'all 0.15s', color: 'var(--text-primary)' },
  score: { fontSize: 64, fontWeight: 700, color: 'var(--accent)', textAlign: 'center', margin: '0 0 8px 0', padding: 0 },
  scoreMax: { fontSize: 13, color: 'var(--text-muted)', textAlign: 'center', margin: '0 0 24px 0', padding: 0 },
  badge: { display: 'inline-block', padding: '8px 16px', background: 'rgba(99,102,241,0.1)', borderRadius: 20, color: 'var(--accent)', fontWeight: 500, margin: '0 0 16px 0' },
  desc: { color: 'var(--text-secondary)', textAlign: 'center', margin: '0 0 32px 0', padding: 0 },
  breakdown: { textAlign: 'left', margin: '0 0 32px 0', padding: 0 },
  breakdownItem: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, background: 'var(--bg-tertiary)', borderRadius: 8, margin: '0 0 8px 0' },
  dots: { display: 'flex', gap: 4, margin: 0, padding: 0 },
  dot: { width: 10, height: 10, borderRadius: '50%', margin: 0, padding: 0 },
  btn: { padding: '12px 24px', margin: 0, background: 'var(--accent)', border: 'none', borderRadius: 8, color: '#fff', fontSize: 14, fontWeight: 500, cursor: 'pointer' },
};

export default function PortfolioScore() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [result, setResult] = useState(null);

  const handleAnswer = async (idx) => {
    const newAnswers = [...answers, 3 - idx];
    setAnswers(newAnswers);
    if (step < 5) {
      setStep(step + 1);
    } else {
      const res = await api(`/api/v1/calculators/portfolio-score?answers=${newAnswers.join(',')}`);
      setResult(res);
    }
  };

  const reset = () => { setStep(0); setAnswers([]); setResult(null); };

  if (result) {
    return (
      <div style={s.card}>
        <div style={{ textAlign: 'center' }}>
          <div style={s.score}>{result.score}</div>
          <div style={s.scoreMax}>out of {result.max_score}</div>
          <div style={s.badge}>{result.personality}</div>
          <p style={s.desc}>{result.description}</p>
        </div>
        <div style={s.breakdown}>
          {result.breakdown.map((b, i) => (
            <div key={i} style={s.breakdownItem}>
              <span style={{ fontSize: 13 }}>{b.question}</span>
              <div style={s.dots}>
                {[...Array(b.max)].map((_, j) => (
                  <div key={j} style={{ ...s.dot, background: j < b.score ? 'var(--accent)' : 'var(--border)' }} />
                ))}
              </div>
            </div>
          ))}
        </div>
        <div style={{ textAlign: 'center' }}>
          <button onClick={reset} style={s.btn}>Retake Assessment</button>
        </div>
      </div>
    );
  }

  return (
    <div style={s.card}>
      <div style={s.header}>
        <h2 style={s.title}>Portfolio Score</h2>
        <span style={s.step}>Question {step + 1} / 6</span>
      </div>
      <div style={s.progress}><div style={{ ...s.progressBar, width: `${((step + 1) / 6) * 100}%` }} /></div>
      <h3 style={s.question}>{questions[step].q}</h3>
      <div style={s.options}>
        {questions[step].opts.map((opt, i) => (
          <button key={i} onClick={() => handleAnswer(i)} style={s.optBtn}
            onMouseEnter={e => e.target.style.borderColor = 'var(--accent)'}
            onMouseLeave={e => e.target.style.borderColor = 'var(--border)'}>
            <span>{opt}</span>
            <ChevronRight style={{ width: 20, height: 20, color: 'var(--text-muted)', margin: 0, padding: 0 }} />
          </button>
        ))}
      </div>
    </div>
  );
}
