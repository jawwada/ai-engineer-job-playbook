import { useState, useEffect, useRef } from "react";

const QUESTIONS = [
  // WORK & RATE
  {
    id: 1, category: "Work & Rate",
    question: "Tap A fills a tank in 12 hours, Tap B in 18 hours. If both are opened together, how long to fill the tank?",
    options: ["6 hrs", "7.2 hrs", "8 hrs", "9 hrs"],
    correct: 1,
    explanation: "Rate A = 1/12, Rate B = 1/18. Combined = 1/12 + 1/18 = 3/36 + 2/36 = 5/36. Time = 36/5 = 7.2 hours."
  },
  {
    id: 2, category: "Work & Rate",
    question: "A can do a job in 20 days, B in 30 days. They work together for 6 days, then A leaves. How many more days does B need to finish?",
    options: ["12", "15", "10", "18"],
    correct: 0,
    explanation: "Combined rate = 1/20 + 1/30 = 1/12 per day. In 6 days: 6/12 = 1/2 done. Remaining = 1/2. B alone: (1/2) ÷ (1/30) = 15? Wait — B's rate is 1/30, so 1/2 ÷ 1/30 = 15. Hmm, let me recheck: 1/2 × 30 = 15. Actually the answer should be 15. Let me fix."
  },
  {
    id: 3, category: "Work & Rate",
    question: "A pipe fills a pool in 8 hours. A leak drains it in 24 hours. With both active, how long to fill the pool?",
    options: ["10 hrs", "12 hrs", "14 hrs", "16 hrs"],
    correct: 1,
    explanation: "Net rate = 1/8 − 1/24 = 3/24 − 1/24 = 2/24 = 1/12. Time = 12 hours."
  },
  {
    id: 4, category: "Work & Rate",
    question: "Machine X produces 300 parts in 6 hrs, Machine Y produces 300 parts in 10 hrs. Working together, how long for 300 parts?",
    options: ["3 hrs", "3.5 hrs", "3.75 hrs", "4 hrs"],
    correct: 2,
    explanation: "X rate = 50/hr, Y rate = 30/hr. Combined = 80/hr. Time = 300/80 = 3.75 hours."
  },
  {
    id: 5, category: "Work & Rate",
    question: "6 workers can build a wall in 10 days. How many workers are needed to build the same wall in 4 days?",
    options: ["12", "15", "18", "20"],
    correct: 1,
    explanation: "Total work = 6 × 10 = 60 worker-days. Workers needed = 60/4 = 15."
  },
  // PROBABILITY
  {
    id: 6, category: "Probability",
    question: "A bag has 5 red, 7 blue, 3 green balls. What's the probability of picking a red or green ball?",
    options: ["1/3", "8/15", "7/15", "2/5"],
    correct: 1,
    explanation: "Total = 15. Favorable = 5 + 3 = 8. P = 8/15."
  },
  {
    id: 7, category: "Probability",
    question: "Two cards are drawn without replacement from a standard deck. What's the probability both are aces?",
    options: ["1/169", "1/221", "1/256", "1/13"],
    correct: 1,
    explanation: "P(1st ace) = 4/52. P(2nd ace | 1st ace) = 3/51. P = 12/2652 = 1/221."
  },
  {
    id: 8, category: "Probability",
    question: "What is the probability of getting at least one head in 3 coin flips?",
    options: ["3/8", "1/2", "7/8", "5/8"],
    correct: 2,
    explanation: "P(no heads) = (1/2)³ = 1/8. P(at least one head) = 1 − 1/8 = 7/8."
  },
  {
    id: 9, category: "Probability",
    question: "A die is rolled twice. What's the probability the sum is exactly 7?",
    options: ["1/6", "5/36", "1/9", "7/36"],
    correct: 0,
    explanation: "Favorable: (1,6),(2,5),(3,4),(4,3),(5,2),(6,1) = 6 outcomes. P = 6/36 = 1/6."
  },
  {
    id: 10, category: "Probability",
    question: "From a group of 4 men and 3 women, a committee of 3 is formed. What's the probability it has exactly 2 men?",
    options: ["12/35", "18/35", "3/7", "15/35"],
    correct: 1,
    explanation: "C(4,2)×C(3,1) / C(7,3) = 6×3 / 35 = 18/35."
  },
  // SPEED, DISTANCE, TIME
  {
    id: 11, category: "Speed & Distance",
    question: "A boat goes 30 km upstream in 5 hrs and 30 km downstream in 3 hrs. What is the speed of the stream?",
    options: ["1 km/h", "2 km/h", "3 km/h", "4 km/h"],
    correct: 1,
    explanation: "Upstream speed = 6, Downstream speed = 10. Stream = (10−6)/2 = 2 km/h."
  },
  {
    id: 12, category: "Speed & Distance",
    question: "A train 150m long passes a pole in 15 seconds. What is its speed in km/h?",
    options: ["30", "36", "40", "45"],
    correct: 1,
    explanation: "Speed = 150/15 = 10 m/s = 10 × 3.6 = 36 km/h."
  },
  {
    id: 13, category: "Speed & Distance",
    question: "Two trains running in opposite directions cross each other in 10 sec. Their speeds are 36 km/h and 54 km/h. Their combined length is?",
    options: ["200m", "225m", "250m", "300m"],
    correct: 2,
    explanation: "Relative speed = 36+54 = 90 km/h = 25 m/s. Distance = 25×10 = 250m."
  },
  {
    id: 14, category: "Speed & Distance",
    question: "A person walks at 5 km/h for 3 hrs, then at 4 km/h for 2 hrs. What's the average speed for the whole journey?",
    options: ["4.4 km/h", "4.5 km/h", "4.6 km/h", "4.8 km/h"],
    correct: 2,
    explanation: "Total distance = 15+8 = 23 km. Total time = 5 hrs. Avg = 23/5 = 4.6 km/h."
  },
  // AVERAGES & DATA
  {
    id: 15, category: "Averages",
    question: "The average of 5 numbers is 42. If one number is removed, the average becomes 40. What was the removed number?",
    options: ["48", "50", "52", "46"],
    correct: 1,
    explanation: "Sum of 5 = 210. Sum of 4 = 160. Removed = 210−160 = 50."
  },
  {
    id: 16, category: "Averages",
    question: "A batsman has a 40-run average after 9 innings. How many runs in the 10th inning to raise the average to 42?",
    options: ["58", "60", "62", "64"],
    correct: 2,
    explanation: "Needed total = 42×10 = 420. Current = 40×9 = 360. Runs needed = 420−360 = 60. Wait: 60. Let me recheck. 420-360=60. The answer is 60."
  },
  {
    id: 17, category: "Averages",
    question: "The median of {12, 7, 3, 15, 9, 21, 6} is:",
    options: ["7", "9", "12", "15"],
    correct: 1,
    explanation: "Sorted: 3, 6, 7, 9, 12, 15, 21. Median (middle) = 9."
  },
  // PERCENTAGES
  {
    id: 18, category: "Percentages",
    question: "A shirt costs $80. It's marked up by 25%, then discounted by 20%. What's the final price?",
    options: ["$80", "$76", "$84", "$78"],
    correct: 0,
    explanation: "After markup: 80 × 1.25 = $100. After discount: 100 × 0.80 = $80."
  },
  {
    id: 19, category: "Percentages",
    question: "A population grows from 50,000 to 60,500 in 2 years at the same annual rate. What's the annual growth rate?",
    options: ["10%", "10.5%", "11%", "12%"],
    correct: 0,
    explanation: "50000 × r² = 60500. r² = 1.21. r = 1.1. Growth rate = 10%."
  },
  {
    id: 20, category: "Percentages",
    question: "If 40% of a number is 120, what is 75% of that number?",
    options: ["200", "225", "240", "250"],
    correct: 1,
    explanation: "Number = 120/0.40 = 300. 75% of 300 = 225."
  },
  // LOGIC
  {
    id: 21, category: "Logic",
    question: "All roses are flowers. Some flowers fade quickly. Which MUST be true?",
    options: [
      "All roses fade quickly",
      "Some roses fade quickly",
      "Some flowers are roses",
      "No roses fade quickly"
    ],
    correct: 2,
    explanation: "Since all roses are flowers, it's definitely true that some flowers are roses. The 'fading' statement says 'some flowers' — we can't know if those include roses."
  },
  {
    id: 22, category: "Logic",
    question: "If it rains, the ground is wet. The ground is wet. What can we conclude?",
    options: [
      "It rained",
      "It might have rained",
      "It didn't rain",
      "It will rain"
    ],
    correct: 1,
    explanation: "This is 'affirming the consequent.' The ground could be wet for other reasons (sprinklers, etc.). We can only say it MIGHT have rained."
  },
  {
    id: 23, category: "Logic",
    question: "In a row of 5 people, A is to the left of B. C is to the right of D. E is between A and C. Who could be in the middle?",
    options: ["A", "E", "B", "D"],
    correct: 1,
    explanation: "E is between A and C, making E a natural middle candidate. The constraints allow: D, A, E, C, B — E is in position 3."
  },
  // RATIOS & PROPORTIONS
  {
    id: 24, category: "Ratios",
    question: "The ratio of boys to girls in a class is 3:5. If there are 24 boys, how many students are in the class?",
    options: ["56", "64", "48", "72"],
    correct: 1,
    explanation: "3 parts = 24, so 1 part = 8. Total = (3+5)×8 = 64."
  },
  {
    id: 25, category: "Ratios",
    question: "A mixture has milk and water in ratio 4:1. To make the ratio 2:1, how much water must be added to 20 litres of mixture?",
    options: ["2 L", "4 L", "3 L", "5 L"],
    correct: 0,
    explanation: "In 20L: Milk = 16L, Water = 4L. For 2:1 ratio with 16L milk, water needed = 8L. Add 8−4 = 4L. Hmm wait: 16:8 = 2:1. So add 4L."
  },
  // NUMBER SERIES
  {
    id: 26, category: "Number Series",
    question: "What comes next: 2, 6, 18, 54, ?",
    options: ["108", "162", "148", "172"],
    correct: 1,
    explanation: "Each term × 3: 2→6→18→54→162."
  },
  {
    id: 27, category: "Number Series",
    question: "What comes next: 1, 4, 9, 16, 25, ?",
    options: ["30", "36", "49", "35"],
    correct: 1,
    explanation: "These are perfect squares: 1², 2², 3², 4², 5², 6² = 36."
  },
  {
    id: 28, category: "Profit & Loss",
    question: "A shopkeeper buys an item for $500 and sells it for $600. What is the profit percentage?",
    options: ["15%", "20%", "25%", "10%"],
    correct: 1,
    explanation: "Profit = 100. Profit % = (100/500)×100 = 20%."
  },
  {
    id: 29, category: "Profit & Loss",
    question: "An article is sold at a 10% loss. If it had been sold for $90 more, there would be a 5% profit. What is the cost price?",
    options: ["$500", "$600", "$700", "$800"],
    correct: 1,
    explanation: "Let CP = x. 0.90x + 90 = 1.05x. 90 = 0.15x. x = 600."
  },
  {
    id: 30, category: "Simple & Compound Interest",
    question: "What is the compound interest on $10,000 at 10% per annum for 2 years?",
    options: ["$2,000", "$2,100", "$2,200", "$1,900"],
    correct: 1,
    explanation: "A = 10000(1.1)² = 10000×1.21 = 12100. CI = 12100−10000 = $2,100."
  },
];

// Fix question 2 and 16 and 25 — corrections
QUESTIONS[1] = {
  id: 2, category: "Work & Rate",
  question: "A can do a job in 20 days, B in 30 days. They work together for 6 days, then A leaves. How many more days does B need to finish?",
  options: ["15", "12", "10", "18"],
  correct: 0,
  explanation: "Combined rate = 1/20 + 1/30 = 5/60 = 1/12 per day. In 6 days: 6/12 = 1/2 done. Remaining = 1/2. B alone: (1/2) ÷ (1/30) = 15 days."
};

QUESTIONS[15] = {
  id: 16, category: "Averages",
  question: "A batsman has a 40-run average after 9 innings. How many runs in the 10th inning to raise the average to 42?",
  options: ["58", "60", "62", "56"],
  correct: 1,
  explanation: "Needed total = 42×10 = 420. Current = 40×9 = 360. Runs needed = 420−360 = 60."
};

QUESTIONS[24] = {
  id: 25, category: "Ratios",
  question: "A mixture has milk and water in ratio 4:1. To make the ratio 2:1, how much water must be added to 20 litres of mixture?",
  options: ["4 L", "2 L", "3 L", "5 L"],
  correct: 0,
  explanation: "In 20L: Milk = 16L, Water = 4L. For 2:1 with 16L milk → water = 8L. Add 8−4 = 4L."
};

const CATEGORIES = [...new Set(QUESTIONS.map(q => q.category))];

const shuffle = (arr) => {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
};

export default function QuantQuiz() {
  const [mode, setMode] = useState("menu"); // menu, quiz, review
  const [selectedCats, setSelectedCats] = useState(new Set(CATEGORIES));
  const [questions, setQuestions] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [selected, setSelected] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [streak, setStreak] = useState(0);
  const [bestStreak, setBestStreak] = useState(0);
  const [totalAttempted, setTotalAttempted] = useState(0);
  const [totalCorrect, setTotalCorrect] = useState(0);
  const [quizSize, setQuizSize] = useState(10);
  const containerRef = useRef(null);

  const startQuiz = () => {
    const filtered = QUESTIONS.filter(q => selectedCats.has(q.category));
    const shuffled = shuffle(filtered).slice(0, quizSize);
    // shuffle options too
    const withShuffledOpts = shuffled.map(q => {
      const indices = q.options.map((_, i) => i);
      const shuffledIndices = shuffle(indices);
      return {
        ...q,
        options: shuffledIndices.map(i => q.options[i]),
        correct: shuffledIndices.indexOf(q.correct),
        originalOptions: q.options,
      };
    });
    setQuestions(withShuffledOpts);
    setCurrentQ(0);
    setSelected(null);
    setShowResult(false);
    setScore(0);
    setAnswers([]);
    setMode("quiz");
  };

  const handleSelect = (idx) => {
    if (showResult) return;
    setSelected(idx);
  };

  const handleSubmit = () => {
    if (selected === null) return;
    const isCorrect = selected === questions[currentQ].correct;
    setShowResult(true);
    if (isCorrect) {
      setScore(s => s + 1);
      setTotalCorrect(c => c + 1);
      setStreak(s => {
        const ns = s + 1;
        if (ns > bestStreak) setBestStreak(ns);
        return ns;
      });
    } else {
      setStreak(0);
    }
    setTotalAttempted(t => t + 1);
    setAnswers(a => [...a, { question: questions[currentQ], selected, isCorrect }]);
  };

  const handleNext = () => {
    if (currentQ + 1 >= questions.length) {
      setMode("review");
    } else {
      setCurrentQ(c => c + 1);
      setSelected(null);
      setShowResult(false);
    }
  };

  const toggleCat = (cat) => {
    setSelectedCats(prev => {
      const n = new Set(prev);
      if (n.has(cat)) { if (n.size > 1) n.delete(cat); }
      else n.add(cat);
      return n;
    });
  };

  const pct = totalAttempted > 0 ? Math.round((totalCorrect / totalAttempted) * 100) : 0;
  const q = questions[currentQ];

  return (
    <div ref={containerRef} style={{
      fontFamily: "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace",
      minHeight: "100vh",
      background: "#0a0a0f",
      color: "#e0e0e8",
      padding: "0",
      boxSizing: "border-box",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes countUp { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
      `}</style>

      {/* HEADER */}
      <div style={{
        background: "linear-gradient(135deg, #12121a 0%, #1a1a2e 100%)",
        borderBottom: "1px solid #2a2a3e",
        padding: "20px 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "12px",
      }}>
        <div>
          <div style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: "20px",
            fontWeight: 700,
            color: "#00ffa3",
            letterSpacing: "-0.5px",
          }}>QUANT DRILL</div>
          <div style={{ fontSize: "11px", color: "#666", marginTop: "2px", letterSpacing: "2px", textTransform: "uppercase" }}>
            Aptitude Training System
          </div>
        </div>
        <div style={{ display: "flex", gap: "20px", fontSize: "12px" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#00ffa3", fontSize: "18px", fontWeight: 700 }}>{totalCorrect}/{totalAttempted}</div>
            <div style={{ color: "#555", fontSize: "10px", letterSpacing: "1px" }}>LIFETIME</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#ff6b6b", fontSize: "18px", fontWeight: 700 }}>{pct}%</div>
            <div style={{ color: "#555", fontSize: "10px", letterSpacing: "1px" }}>ACCURACY</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#ffd93d", fontSize: "18px", fontWeight: 700 }}>{bestStreak}</div>
            <div style={{ color: "#555", fontSize: "10px", letterSpacing: "1px" }}>BEST STREAK</div>
          </div>
        </div>
      </div>

      <div style={{ padding: "24px", maxWidth: "720px", margin: "0 auto" }}>

        {/* MENU */}
        {mode === "menu" && (
          <div style={{ animation: "fadeUp 0.4s ease" }}>
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "15px",
              fontWeight: 600,
              color: "#888",
              marginBottom: "16px",
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}>Select Topics</div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "28px" }}>
              {CATEGORIES.map(cat => (
                <button key={cat} onClick={() => toggleCat(cat)} style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: selectedCats.has(cat) ? "1px solid #00ffa3" : "1px solid #2a2a3e",
                  background: selectedCats.has(cat) ? "rgba(0,255,163,0.08)" : "transparent",
                  color: selectedCats.has(cat) ? "#00ffa3" : "#666",
                  cursor: "pointer",
                  fontSize: "12px",
                  fontFamily: "inherit",
                  fontWeight: 500,
                  transition: "all 0.2s",
                }}>{cat}</button>
              ))}
            </div>

            <div style={{ marginBottom: "28px" }}>
              <div style={{ fontSize: "12px", color: "#666", marginBottom: "10px", letterSpacing: "1px", textTransform: "uppercase" }}>
                Questions per round
              </div>
              <div style={{ display: "flex", gap: "8px" }}>
                {[5, 10, 15, 20].map(n => (
                  <button key={n} onClick={() => setQuizSize(n)} style={{
                    padding: "10px 20px",
                    borderRadius: "6px",
                    border: quizSize === n ? "1px solid #00ffa3" : "1px solid #2a2a3e",
                    background: quizSize === n ? "rgba(0,255,163,0.08)" : "transparent",
                    color: quizSize === n ? "#00ffa3" : "#666",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontFamily: "inherit",
                    fontWeight: 600,
                    transition: "all 0.2s",
                  }}>{n}</button>
                ))}
              </div>
            </div>

            <button onClick={startQuiz} style={{
              width: "100%",
              padding: "16px",
              borderRadius: "8px",
              border: "none",
              background: "linear-gradient(135deg, #00ffa3 0%, #00cc82 100%)",
              color: "#0a0a0f",
              fontSize: "14px",
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 700,
              cursor: "pointer",
              letterSpacing: "2px",
              textTransform: "uppercase",
              transition: "transform 0.15s",
            }}
              onMouseDown={e => e.currentTarget.style.transform = "scale(0.98)"}
              onMouseUp={e => e.currentTarget.style.transform = "scale(1)"}
            >
              START DRILL →
            </button>

            <div style={{ marginTop: "20px", fontSize: "11px", color: "#444", textAlign: "center" }}>
              {QUESTIONS.filter(q => selectedCats.has(q.category)).length} questions available in selected topics
            </div>
          </div>
        )}

        {/* QUIZ */}
        {mode === "quiz" && q && (
          <div style={{ animation: "fadeUp 0.35s ease" }} key={currentQ}>
            {/* Progress */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "11px", color: "#555", letterSpacing: "1px" }}>
                Q {currentQ + 1} / {questions.length}
              </span>
              <span style={{
                fontSize: "11px",
                padding: "3px 10px",
                borderRadius: "4px",
                background: "rgba(0,255,163,0.08)",
                color: "#00ffa3",
                border: "1px solid rgba(0,255,163,0.2)",
              }}>{q.category}</span>
              {streak > 1 && (
                <span style={{
                  fontSize: "11px",
                  color: "#ffd93d",
                  animation: "pulse 1.5s infinite",
                }}>🔥 {streak} streak</span>
              )}
            </div>

            <div style={{
              width: "100%",
              height: "3px",
              background: "#1a1a2e",
              borderRadius: "2px",
              marginBottom: "24px",
              overflow: "hidden",
            }}>
              <div style={{
                width: `${((currentQ + (showResult ? 1 : 0)) / questions.length) * 100}%`,
                height: "100%",
                background: "#00ffa3",
                borderRadius: "2px",
                transition: "width 0.4s ease",
              }} />
            </div>

            {/* Question */}
            <div style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "17px",
              fontWeight: 500,
              lineHeight: 1.6,
              color: "#e0e0e8",
              marginBottom: "24px",
              padding: "20px",
              background: "#12121a",
              borderRadius: "10px",
              border: "1px solid #1e1e30",
            }}>
              {q.question}
            </div>

            {/* Options */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "20px" }}>
              {q.options.map((opt, idx) => {
                let bg = "transparent";
                let border = "1px solid #2a2a3e";
                let color = "#ccc";
                if (showResult) {
                  if (idx === q.correct) {
                    bg = "rgba(0,255,163,0.1)";
                    border = "1px solid #00ffa3";
                    color = "#00ffa3";
                  } else if (idx === selected && idx !== q.correct) {
                    bg = "rgba(255,107,107,0.1)";
                    border = "1px solid #ff6b6b";
                    color = "#ff6b6b";
                  }
                } else if (idx === selected) {
                  bg = "rgba(100,100,255,0.08)";
                  border = "1px solid #6666ff";
                  color = "#aaaaff";
                }
                return (
                  <button key={idx} onClick={() => handleSelect(idx)} style={{
                    padding: "14px 18px",
                    borderRadius: "8px",
                    border,
                    background: bg,
                    color,
                    cursor: showResult ? "default" : "pointer",
                    fontSize: "14px",
                    fontFamily: "inherit",
                    textAlign: "left",
                    transition: "all 0.2s",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    animation: `slideIn 0.3s ease ${idx * 0.06}s both`,
                  }}>
                    <span style={{
                      width: "28px",
                      height: "28px",
                      borderRadius: "50%",
                      border: "1px solid currentColor",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "12px",
                      fontWeight: 600,
                      flexShrink: 0,
                      opacity: 0.7,
                    }}>{String.fromCharCode(65 + idx)}</span>
                    {opt}
                  </button>
                );
              })}
            </div>

            {/* Explanation */}
            {showResult && (
              <div style={{
                padding: "16px",
                borderRadius: "8px",
                background: "#12121a",
                border: "1px solid #2a2a3e",
                marginBottom: "20px",
                animation: "fadeUp 0.3s ease",
              }}>
                <div style={{
                  fontSize: "11px",
                  color: selected === q.correct ? "#00ffa3" : "#ff6b6b",
                  fontWeight: 700,
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                  marginBottom: "8px",
                }}>
                  {selected === q.correct ? "✓ CORRECT" : "✗ INCORRECT"}
                </div>
                <div style={{
                  fontSize: "13px",
                  lineHeight: 1.7,
                  color: "#999",
                }}>
                  {q.explanation}
                </div>
              </div>
            )}

            {/* Action buttons */}
            {!showResult ? (
              <button onClick={handleSubmit} disabled={selected === null} style={{
                width: "100%",
                padding: "14px",
                borderRadius: "8px",
                border: "none",
                background: selected !== null ? "#00ffa3" : "#1a1a2e",
                color: selected !== null ? "#0a0a0f" : "#444",
                fontSize: "13px",
                fontFamily: "'Space Grotesk', sans-serif",
                fontWeight: 700,
                cursor: selected !== null ? "pointer" : "not-allowed",
                letterSpacing: "2px",
                textTransform: "uppercase",
                transition: "all 0.2s",
              }}>CHECK ANSWER</button>
            ) : (
              <button onClick={handleNext} style={{
                width: "100%",
                padding: "14px",
                borderRadius: "8px",
                border: "1px solid #2a2a3e",
                background: "transparent",
                color: "#e0e0e8",
                fontSize: "13px",
                fontFamily: "'Space Grotesk', sans-serif",
                fontWeight: 600,
                cursor: "pointer",
                letterSpacing: "2px",
                textTransform: "uppercase",
                transition: "all 0.2s",
              }}>
                {currentQ + 1 >= questions.length ? "VIEW RESULTS →" : "NEXT →"}
              </button>
            )}

            <div style={{ textAlign: "center", marginTop: "16px" }}>
              <span style={{ fontSize: "13px", color: "#00ffa3", fontWeight: 600 }}>{score}</span>
              <span style={{ fontSize: "12px", color: "#444" }}> / {currentQ + (showResult ? 1 : 0)} correct</span>
            </div>
          </div>
        )}

        {/* REVIEW */}
        {mode === "review" && (
          <div style={{ animation: "fadeUp 0.4s ease" }}>
            <div style={{
              textAlign: "center",
              padding: "32px 20px",
              background: "linear-gradient(135deg, #12121a, #1a1a2e)",
              borderRadius: "12px",
              border: "1px solid #2a2a3e",
              marginBottom: "24px",
            }}>
              <div style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: "48px",
                fontWeight: 700,
                color: score / questions.length >= 0.7 ? "#00ffa3" : score / questions.length >= 0.4 ? "#ffd93d" : "#ff6b6b",
                animation: "countUp 0.5s ease",
              }}>
                {score}/{questions.length}
              </div>
              <div style={{ fontSize: "13px", color: "#666", marginTop: "8px" }}>
                {score / questions.length >= 0.9 ? "Outstanding! 🏆" :
                 score / questions.length >= 0.7 ? "Great work! Keep it up." :
                 score / questions.length >= 0.4 ? "Getting there. Review the ones below." :
                 "Keep practicing — you'll improve fast."}
              </div>
            </div>

            {/* Wrong answers */}
            {answers.filter(a => !a.isCorrect).length > 0 && (
              <>
                <div style={{
                  fontSize: "12px",
                  color: "#ff6b6b",
                  fontWeight: 600,
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                  marginBottom: "12px",
                }}>REVIEW MISTAKES ({answers.filter(a => !a.isCorrect).length})</div>
                {answers.filter(a => !a.isCorrect).map((a, i) => (
                  <div key={i} style={{
                    padding: "16px",
                    borderRadius: "8px",
                    background: "#12121a",
                    border: "1px solid #1e1e30",
                    marginBottom: "10px",
                    animation: `fadeUp 0.3s ease ${i * 0.08}s both`,
                  }}>
                    <div style={{ fontSize: "13px", color: "#ccc", marginBottom: "8px", lineHeight: 1.5 }}>
                      {a.question.question}
                    </div>
                    <div style={{ fontSize: "12px", color: "#ff6b6b", marginBottom: "4px" }}>
                      Your answer: {a.question.options[a.selected]}
                    </div>
                    <div style={{ fontSize: "12px", color: "#00ffa3", marginBottom: "8px" }}>
                      Correct: {a.question.options[a.question.correct]}
                    </div>
                    <div style={{ fontSize: "11px", color: "#666", lineHeight: 1.6 }}>
                      {a.question.explanation}
                    </div>
                  </div>
                ))}
              </>
            )}

            {answers.filter(a => a.isCorrect).length > 0 && (
              <>
                <div style={{
                  fontSize: "12px",
                  color: "#00ffa3",
                  fontWeight: 600,
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                  marginBottom: "12px",
                  marginTop: "24px",
                }}>CORRECT ({answers.filter(a => a.isCorrect).length})</div>
                {answers.filter(a => a.isCorrect).map((a, i) => (
                  <div key={i} style={{
                    padding: "12px 16px",
                    borderRadius: "8px",
                    background: "#12121a",
                    border: "1px solid #1a2a1e",
                    marginBottom: "6px",
                    fontSize: "12px",
                    color: "#777",
                    animation: `fadeUp 0.3s ease ${i * 0.05}s both`,
                  }}>
                    ✓ {a.question.question.substring(0, 80)}...
                  </div>
                ))}
              </>
            )}

            <button onClick={() => setMode("menu")} style={{
              width: "100%",
              padding: "16px",
              borderRadius: "8px",
              border: "none",
              background: "linear-gradient(135deg, #00ffa3 0%, #00cc82 100%)",
              color: "#0a0a0f",
              fontSize: "14px",
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 700,
              cursor: "pointer",
              letterSpacing: "2px",
              textTransform: "uppercase",
              marginTop: "24px",
            }}>
              DRILL AGAIN →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
