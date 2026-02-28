'use client';
import { useState } from 'react';
import { ChevronRight, RotateCcw, Trophy, Target, TrendingUp, Shield, Calendar, PieChart } from 'lucide-react';
import { C, sCard, useCompact } from './theme';

const questions = [
  { q: "How well do you know your current Equity vs. Debt allocation?", icon: PieChart, opts: ["I know the exact ratio (e.g., 60:40)", "I have a rough estimate", "I don't actively track it", "I have never checked"] },
  { q: "How diversified is your portfolio across asset classes?", icon: Target, opts: ["Very diversified (5+ asset classes)", "Moderately diversified (3-4)", "Somewhat diversified (2)", "Not diversified (1)"] },
  { q: "Do you have an emergency fund?", icon: Shield, opts: ["Yes, 6+ months expenses", "Yes, 3-6 months", "Yes, less than 3 months", "No emergency fund"] },
  { q: "How regularly do you invest?", icon: Calendar, opts: ["Monthly SIP/automatic", "Quarterly", "Occasionally", "Rarely/Never"] },
  { q: "Are your investments aligned with specific goals?", icon: Target, opts: ["Yes, all mapped to goals", "Most are goal-based", "Some are goal-based", "No specific goals"] },
  { q: "How often do you review your portfolio?", icon: TrendingUp, opts: ["Monthly", "Quarterly", "Yearly", "Never"] },
];

const personalities = [
  { min: 0, max: 8, name: 'Needs Attention', color: '#ef4444', desc: 'Your portfolio needs significant improvements. Consider consulting a financial advisor.' },
  { min: 9, max: 14, name: 'Building Up', color: '#f59e0b', desc: 'You have a foundation but there\'s room for improvement in diversification and discipline.' },
  { min: 15, max: 20, name: 'Well Managed', color: '#3b82f6', desc: 'Good job! Your portfolio is on track. Minor tweaks can optimize returns.' },
  { min: 21, max: 24, name: 'Expert Level', color: '#10b981', desc: 'Excellent! You have a well-structured, disciplined investment approach.' },
];

export default function PortfolioScore() {
  const compact = useCompact();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [hoveredOpt, setHoveredOpt] = useState(null);

  const handleAnswer = (idx) => {
    const score = 4 - idx; // 4 for best, 1 for worst
    const newAnswers = [...answers, score];
    setAnswers(newAnswers);
    if (step < 5) setStep(step + 1);
  };

  const reset = () => { setStep(0); setAnswers([]); };

  const totalScore = answers.reduce((s, a) => s + a, 0);
  const maxScore = 24;
  const personality = personalities.find(p => totalScore >= p.min && totalScore <= p.max) || personalities[0];
  const pct = Math.round((totalScore / maxScore) * 100);
  const done = answers.length === 6;
  const Icon = questions[step]?.icon || Target;

  if (done) {
    return (
      <div style={{ maxWidth: 600, margin: '0 auto', padding: 0 }}>
        <div style={{ ...sCard, textAlign: 'center', padding: 40 }}>
          {/* Score Circle */}
          <div style={{ position: 'relative', width: 180, height: 180, margin: '0 auto 24px' }}>
            <svg width="180" height="180" style={{ transform: 'rotate(-90deg)' }}>
              <circle cx="90" cy="90" r="80" stroke="var(--bg-tertiary)" strokeWidth="12" fill="none" />
              <circle cx="90" cy="90" r="80" stroke={personality.color} strokeWidth="12" fill="none"
                strokeDasharray={`${pct * 5.03} 503`} strokeLinecap="round" style={{ transition: 'stroke-dasharray 0.8s ease' }} />
            </svg>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ fontSize: 48, fontWeight: 700, color: personality.color }}>{totalScore}</span>
              <span style={{ fontSize: 14, color: C.textMuted }}>out of {maxScore}</span>
            </div>
          </div>

          {/* Personality Badge */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 20px', background: `${personality.color}15`, borderRadius: 24, marginBottom: 16 }}>
            <Trophy style={{ width: 18, height: 18, color: personality.color }} />
            <span style={{ fontSize: 16, fontWeight: 600, color: personality.color }}>{personality.name}</span>
          </div>

          <p style={{ fontSize: 15, color: C.textSec, lineHeight: 1.6, margin: '0 0 32px 0', maxWidth: 400, marginLeft: 'auto', marginRight: 'auto' }}>{personality.desc}</p>

          {/* Breakdown */}
          <div style={{ background: C.cardAlt, borderRadius: 12, padding: 20, textAlign: 'left', marginBottom: 24 }}>
            <h4 style={{ fontSize: 13, fontWeight: 600, color: C.textMuted, margin: '0 0 16px 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Score Breakdown</h4>
            {questions.map((q, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 0', borderBottom: i < 5 ? `1px solid ${C.border}` : 'none' }}>
                <span style={{ fontSize: 13, color: C.textSec, flex: 1, paddingRight: 12 }}>{q.q.split('?')[0]}?</span>
                <div style={{ display: 'flex', gap: 4 }}>
                  {[1, 2, 3, 4].map(dot => (
                    <div key={dot} style={{ width: 10, height: 10, borderRadius: '50%', background: dot <= answers[i] ? personality.color : C.border }} />
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button onClick={reset} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '12px 28px', background: C.accent, border: 'none', borderRadius: 10, color: '#fff', fontSize: 15, fontWeight: 600, cursor: 'pointer' }}>
            <RotateCcw style={{ width: 16, height: 16 }} /> Retake Assessment
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 0 }}>
      <div style={sCard}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>StockPilot Score</h2>
          <span style={{ fontSize: 14, color: C.textMuted, fontWeight: 500 }}>Question {step + 1} / 6</span>
        </div>

        {/* Progress */}
        <div style={{ height: 6, background: C.cardAlt, borderRadius: 3, marginBottom: 32, overflow: 'hidden' }}>
          <div style={{ height: '100%', background: C.accent, borderRadius: 3, width: `${((step + 1) / 6) * 100}%`, transition: 'width 0.3s ease' }} />
        </div>

        {/* Question */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 28 }}>
          <div style={{ padding: 12, background: `${C.accent}15`, borderRadius: 12, color: C.accent }}><Icon style={{ width: 24, height: 24 }} /></div>
          <h3 style={{ fontSize: 20, fontWeight: 600, color: C.text, margin: 0, lineHeight: 1.4 }}>{questions[step].q}</h3>
        </div>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {questions[step].opts.map((opt, i) => (
            <button key={i} onClick={() => handleAnswer(i)}
              onMouseEnter={() => setHoveredOpt(i)} onMouseLeave={() => setHoveredOpt(null)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px',
                background: hoveredOpt === i ? C.cardAlt : 'transparent', border: `1px solid ${hoveredOpt === i ? C.accent : C.border}`,
                borderRadius: 12, fontSize: 15, textAlign: 'left', cursor: 'pointer', color: C.text, transition: 'all 0.15s',
              }}>
              <span>{opt}</span>
              <ChevronRight style={{ width: 18, height: 18, color: hoveredOpt === i ? C.accent : C.textMuted }} />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
