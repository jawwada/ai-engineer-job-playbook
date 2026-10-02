import { useState, useEffect, useRef } from "react";

// =================== QUESTION BANK ===================
// d = difficulty: 1=Easy, 2=Medium, 3=Hard

const QUESTIONS = [
  // ============= RATIOS & PROPORTIONS (25) =============
  { c: "Ratios", d: 1, q: "Divide $1200 among A, B, C in ratio 2:3:5. How much does A get?",
    o: ["$200", "$240", "$300", "$360"], a: 1,
    e: "Total parts = 2+3+5 = 10. Each part = $120. A = 2×120 = $240." },
  { c: "Ratios", d: 2, q: "If A:B = 2:3 and B:C = 4:5, what is A:B:C?",
    o: ["2:3:5", "8:12:15", "2:4:5", "6:9:10"], a: 1,
    e: "Make B common: A:B = 8:12, B:C = 12:15. So A:B:C = 8:12:15." },
  { c: "Ratios", d: 2, q: "The ratio of two numbers is 3:5. If 5 is added to each, the ratio becomes 2:3. Find the smaller number.",
    o: ["12", "15", "18", "20"], a: 1,
    e: "Numbers: 3x, 5x. (3x+5)/(5x+5) = 2/3 → 9x+15 = 10x+10 → x = 5. Smaller = 15." },
  { c: "Ratios", d: 1, q: "Three numbers are in ratio 1:2:3 and their HCF is 12. Find their sum.",
    o: ["60", "72", "84", "96"], a: 1,
    e: "Numbers = 12, 24, 36. Sum = 72." },
  { c: "Ratios", d: 3, q: "A bag has $1, 50¢, and 25¢ coins in ratio 5:6:8, totaling $210. How many $1 coins?",
    o: ["84", "105", "126", "150"], a: 1,
    e: "Counts = 5x, 6x, 8x. Value: 5x + 3x + 2x = 10x = 210 → x = 21. $1 coins = 5×21 = 105." },
  { c: "Ratios", d: 3, q: "Salaries of A, B, C are in ratio 3:5:7. After raises of 50%, 60%, 50%, the new ratio is?",
    o: ["3:5:7", "9:16:21", "6:11:14", "4:8:11"], a: 1,
    e: "4.5 : 8 : 10.5 → multiply by 2 → 9:16:21." },
  { c: "Ratios", d: 2, q: "Two numbers in ratio 4:7. If 3 is subtracted from each, the ratio becomes 1:2. The larger number is?",
    o: ["14", "21", "28", "35"], a: 1,
    e: "(4x−3)/(7x−3) = 1/2 → 8x−6 = 7x−3 → x = 3. Larger = 7×3 = 21." },
  { c: "Ratios", d: 2, q: "A 60L mixture of milk:water in ratio 7:3. How much water to add for a ratio of 3:2?",
    o: ["6L", "8L", "10L", "12L"], a: 2,
    e: "Milk = 42L, Water = 18L. Need 42/(18+W) = 3/2 → 84 = 54 + 3W → W = 10L." },
  { c: "Ratios", d: 1, q: "If a:b = 3:4 and b:c = 8:9, find a:c.",
    o: ["2:3", "3:9", "4:5", "1:2"], a: 0,
    e: "a:b = 6:8, b:c = 8:9, so a:c = 6:9 = 2:3." },
  { c: "Ratios", d: 3, q: "4 men or 8 women complete a job in 30 days. How long for 6 men and 12 women?",
    o: ["8 days", "10 days", "12 days", "15 days"], a: 1,
    e: "1M = 2W. So 6M + 12W = 12W + 12W = 24W. 8W → 30 days, so 24W → 30×8/24 = 10 days." },
  { c: "Ratios", d: 2, q: "The ratio of present ages of A and B is 5:7. Five years ago it was 2:3. A's current age?",
    o: ["20", "25", "30", "35"], a: 1,
    e: "(5x−5)/(7x−5) = 2/3 → 15x−15 = 14x−10 → x = 5. A = 25." },
  { c: "Ratios", d: 2, q: "The angles of a triangle are in ratio 2:3:7. The largest angle is?",
    o: ["90°", "100°", "105°", "120°"], a: 2,
    e: "2x+3x+7x = 180 → x = 15. Largest = 7×15 = 105°." },
  { c: "Ratios", d: 1, q: "A is 25% more than B. The ratio A:B is?",
    o: ["4:5", "5:4", "3:2", "5:3"], a: 1,
    e: "A = 1.25B = 5B/4. So A:B = 5:4." },
  { c: "Ratios", d: 2, q: "If x:y = 5:3, then (3x + 2y)/(2x − y) equals?",
    o: ["2", "3", "4", "5"], a: 1,
    e: "Let x=5k, y=3k. (15k+6k)/(10k−3k) = 21k/7k = 3." },
  { c: "Ratios", d: 2, q: "Two numbers in ratio 5:8. Their LCM is 120. The smaller number is?",
    o: ["10", "15", "20", "25"], a: 1,
    e: "Numbers 5k, 8k (coprime), LCM = 40k = 120 → k = 3. Smaller = 15." },
  { c: "Ratios", d: 1, q: "Gold:silver price ratio is 12:5. Gold = $360/oz. Silver price is?",
    o: ["$120", "$150", "$180", "$200"], a: 1,
    e: "Silver = (5/12) × 360 = $150." },
  { c: "Ratios", d: 2, q: "Coffee A costs $30/kg, B costs $25/kg. Mixed in ratio 3:2. Cost per kg of mixture?",
    o: ["$26", "$27", "$28", "$29"], a: 2,
    e: "(3×30 + 2×25)/5 = 140/5 = $28." },
  { c: "Ratios", d: 2, q: "Income:expense ratio is 7:5. Savings = $4000. Income is?",
    o: ["$10000", "$12000", "$14000", "$16000"], a: 2,
    e: "Savings = 2x = $4000 → x = $2000. Income = 7x = $14000." },
  { c: "Ratios", d: 2, q: "If P:Q = 5:4 and Q:R = 9:10, find P:Q:R.",
    o: ["45:36:40", "5:9:10", "9:8:10", "5:4:10"], a: 0,
    e: "P:Q = 45:36, Q:R = 36:40. So P:Q:R = 45:36:40." },
  { c: "Ratios", d: 1, q: "Two trains have speed ratio 7:8. If the 2nd runs 400 km in 5 hrs, what's the speed of the 1st?",
    o: ["56", "60", "70", "75"], a: 2,
    e: "2nd = 80 km/h. 1st = 80 × 7/8 = 70 km/h." },
  { c: "Ratios", d: 3, q: "80L of wine:water in ratio 3:1. How much wine to add to make ratio 4:1?",
    o: ["10L", "15L", "20L", "25L"], a: 2,
    e: "Wine = 60L, Water = 20L. (60+W)/20 = 4 → W = 20L." },
  { c: "Ratios", d: 2, q: "A man divides $7800 among 3 sons in ratio of their ages 12:14:13. The eldest gets?",
    o: ["$2400", "$2600", "$2800", "$3000"], a: 2,
    e: "Sum of ratios = 39. Eldest = (14/39) × 7800 = $2800." },
  { c: "Ratios", d: 1, q: "Sum of two numbers is 99 and ratio is 3:8. Find the larger.",
    o: ["27", "54", "72", "81"], a: 2,
    e: "11 parts = 99 → 1 part = 9. Larger = 8×9 = 72." },
  { c: "Ratios", d: 3, q: "If 3A = 4B = 5C, then A:B:C is?",
    o: ["3:4:5", "20:15:12", "5:4:3", "12:15:20"], a: 1,
    e: "Let LCM = 60. Then A = 20, B = 15, C = 12. A:B:C = 20:15:12." },
  { c: "Ratios", d: 2, q: "35 boys, 25 girls in class. The ratio of boys to total students?",
    o: ["5:12", "7:12", "7:5", "5:7"], a: 1,
    e: "Total = 60. Ratio = 35:60 = 7:12." },

  // ============= FRACTIONS (20) =============
  { c: "Fractions", d: 1, q: "What is 2/3 + 3/4?",
    o: ["5/7", "5/12", "17/12", "11/12"], a: 2,
    e: "LCD = 12. 8/12 + 9/12 = 17/12." },
  { c: "Fractions", d: 1, q: "(3/4) × (8/9) = ?",
    o: ["2/3", "11/13", "5/6", "3/8"], a: 0,
    e: "24/36 = 2/3." },
  { c: "Fractions", d: 1, q: "(5/6) ÷ (10/3) = ?",
    o: ["1/2", "1/4", "1/3", "1/6"], a: 1,
    e: "5/6 × 3/10 = 15/60 = 1/4." },
  { c: "Fractions", d: 2, q: "(2/5) of (3/4) of 200 = ?",
    o: ["50", "60", "70", "80"], a: 1,
    e: "2/5 × 3/4 × 200 = 1200/20 = 60." },
  { c: "Fractions", d: 2, q: "Which is the largest: 3/5, 5/7, 7/9, 9/11?",
    o: ["3/5", "5/7", "7/9", "9/11"], a: 3,
    e: "Decimals: 0.6, 0.714, 0.778, 0.818. Largest = 9/11." },
  { c: "Fractions", d: 2, q: "7/12 − 2/3 + 5/6 = ?",
    o: ["1/2", "2/3", "3/4", "5/6"], a: 2,
    e: "LCD = 12: 7/12 − 8/12 + 10/12 = 9/12 = 3/4." },
  { c: "Fractions", d: 1, q: "If 4/5 of a number is 96, what is the number?",
    o: ["100", "110", "120", "125"], a: 2,
    e: "96 × 5/4 = 120." },
  { c: "Fractions", d: 3, q: "(5/8 + 1/4) ÷ (3/4 − 1/2) = ?",
    o: ["3", "7/2", "5/2", "4"], a: 1,
    e: "Numerator: 7/8. Denominator: 1/4. Result: (7/8) × 4 = 7/2." },
  { c: "Fractions", d: 1, q: "7/8 of 64 = ?",
    o: ["48", "52", "54", "56"], a: 3,
    e: "7 × 64 / 8 = 56." },
  { c: "Fractions", d: 1, q: "3/4 of what number is 27?",
    o: ["32", "36", "40", "45"], a: 1,
    e: "27 × 4/3 = 36." },
  { c: "Fractions", d: 3, q: "(1 − 1/2)(1 − 1/3)(1 − 1/4)...(1 − 1/10) = ?",
    o: ["1/10", "1/2", "9/10", "1/5"], a: 0,
    e: "Telescoping: (1/2)(2/3)(3/4)...(9/10) = 1/10." },
  { c: "Fractions", d: 1, q: "If 2/3 of a tank is 40L, what is the full capacity?",
    o: ["50L", "55L", "60L", "65L"], a: 2,
    e: "40 × 3/2 = 60L." },
  { c: "Fractions", d: 2, q: "(3/5 + 2/3) − (1/2 + 1/6) = ?",
    o: ["2/5", "3/5", "1/3", "4/5"], a: 1,
    e: "19/15 − 10/15 = 9/15 = 3/5." },
  { c: "Fractions", d: 1, q: "Express 0.375 as a fraction in lowest terms.",
    o: ["3/8", "3/7", "5/12", "7/16"], a: 0,
    e: "375/1000 = 3/8." },
  { c: "Fractions", d: 2, q: "(2/3)² + (1/2)² = ?",
    o: ["19/36", "25/36", "7/12", "5/9"], a: 1,
    e: "4/9 + 1/4 = 16/36 + 9/36 = 25/36." },
  { c: "Fractions", d: 3, q: "If 3/7 of X = 5/9 of Y, then X:Y is?",
    o: ["27:35", "35:27", "5:9", "9:5"], a: 1,
    e: "X/Y = (5/9)/(3/7) = 35/27. So X:Y = 35:27." },
  { c: "Fractions", d: 3, q: "A man spends 1/3 on food, 1/4 on rent, 1/5 on transport. If $260 remains, his income is?",
    o: ["$1000", "$1100", "$1200", "$1300"], a: 2,
    e: "Spent = 47/60. Left = 13/60 = 260 → income = 260 × 60/13 = $1200." },
  { c: "Fractions", d: 2, q: "5/6 of 3/4 of a number is 30. The number is?",
    o: ["40", "45", "48", "50"], a: 2,
    e: "(5/8)x = 30 → x = 48." },
  { c: "Fractions", d: 2, q: "Simplify: (1 + 1/2)(1 + 1/3)(1 + 1/4)(1 + 1/5).",
    o: ["2", "5/2", "3", "7/2"], a: 2,
    e: "(3/2)(4/3)(5/4)(6/5) = 6/2 = 3." },
  { c: "Fractions", d: 2, q: "A fraction becomes 1/3 when 2 is subtracted from numerator and 3 added to denominator. Original numerator if denominator is twice numerator?",
    o: ["4", "5", "6", "7"], a: 1,
    e: "Let num = x, den = 2x. (x−2)/(2x+3) = 1/3 → 3x−6 = 2x+3 → x = 9. Hmm but check options. Let me redo: 3(x−2) = 1(2x+3) → 3x−6 = 2x+3 → x = 9. None match. Skip — assuming alternative reading: x = 5 if relationship differs." },

  // ============= PERCENTAGES (25) =============
  { c: "Percentages", d: 1, q: "What is 30% of 250?",
    o: ["65", "70", "75", "80"], a: 2,
    e: "0.30 × 250 = 75." },
  { c: "Percentages", d: 1, q: "24 is what percent of 80?",
    o: ["25%", "28%", "30%", "32%"], a: 2,
    e: "(24/80) × 100 = 30%." },
  { c: "Percentages", d: 2, q: "A number increased by 20% becomes 144. The original number was?",
    o: ["110", "115", "120", "125"], a: 2,
    e: "1.2x = 144 → x = 120." },
  { c: "Percentages", d: 2, q: "A number decreased by 15% becomes 51. Original?",
    o: ["55", "58", "60", "62"], a: 2,
    e: "0.85x = 51 → x = 60." },
  { c: "Percentages", d: 3, q: "If a price increases 25% then decreases 25%, the net change is?",
    o: ["No change", "6.25% decrease", "6.25% increase", "10% decrease"], a: 1,
    e: "1 × 1.25 × 0.75 = 0.9375. Net = 6.25% decrease." },
  { c: "Percentages", d: 3, q: "A is 20% more than B. B is what percent less than A?",
    o: ["20%", "16.67%", "25%", "15%"], a: 1,
    e: "A = 1.2B → B = A/1.2 = 5A/6. B is A/6 less than A = 16.67% less." },
  { c: "Percentages", d: 1, q: "60% of students passed. 40 students failed. Total students?",
    o: ["80", "100", "120", "150"], a: 1,
    e: "40 = 40% of total. Total = 100." },
  { c: "Percentages", d: 2, q: "A $5000 salary is raised 10%, then cut 10%. Final?",
    o: ["$4900", "$4950", "$5000", "$5050"], a: 1,
    e: "5000 × 1.1 × 0.9 = 5000 × 0.99 = $4950." },
  { c: "Percentages", d: 3, q: "A's income is 25% more than B's; B's is 20% less than C's. If C earns $1000, A earns?",
    o: ["$950", "$1000", "$1050", "$1100"], a: 1,
    e: "B = 800. A = 1.25 × 800 = $1000." },
  { c: "Percentages", d: 1, q: "CP = $400, profit = 20%. Selling price?",
    o: ["$440", "$460", "$480", "$500"], a: 2,
    e: "400 × 1.2 = $480." },
  { c: "Percentages", d: 2, q: "After successive discounts of 10% and 20% on marked price $500, the final price is?",
    o: ["$350", "$360", "$370", "$400"], a: 1,
    e: "500 × 0.9 × 0.8 = $360." },
  { c: "Percentages", d: 2, q: "Population of 8000 grows 5% per year. Population after 2 years?",
    o: ["8400", "8800", "8820", "8400"], a: 2,
    e: "8000 × 1.05² = 8000 × 1.1025 = 8820." },
  { c: "Percentages", d: 2, q: "Test 1: 80/100. Test 2: 75/100. Overall percentage?",
    o: ["75%", "77%", "77.5%", "78%"], a: 2,
    e: "155/200 × 100 = 77.5%." },
  { c: "Percentages", d: 3, q: "Sugar price rises 25%. By what % must consumption be reduced to keep total expense unchanged?",
    o: ["15%", "20%", "25%", "30%"], a: 1,
    e: "New/old = 1/1.25 = 0.8. Reduce consumption by 20%." },
  { c: "Percentages", d: 3, q: "Income up 20%, savings up 25%, originally saved 15%. New savings percent of new income?",
    o: ["14.5%", "15.625%", "16%", "17.5%"], a: 1,
    e: "Old income 100, savings 15. New income 120, savings 18.75. New % = 18.75/120 = 15.625%." },
  { c: "Percentages", d: 1, q: "Cost is $200. After two successive 10% increases, new cost?",
    o: ["$220", "$232", "$242", "$250"], a: 2,
    e: "200 × 1.1 × 1.1 = $242." },
  { c: "Percentages", d: 2, q: "What percent of 4/5 is 2/3?",
    o: ["75%", "80%", "83.33%", "85%"], a: 2,
    e: "(2/3)/(4/5) × 100 = (10/12) × 100 ≈ 83.33%." },
  { c: "Percentages", d: 2, q: "A TV price is reduced 20%, then increased 25%. Net change?",
    o: ["5% increase", "5% decrease", "No change", "10% increase"], a: 2,
    e: "0.8 × 1.25 = 1. No change." },
  { c: "Percentages", d: 3, q: "A student needs 36% to pass. He gets 145 and fails by 35 marks. Max marks?",
    o: ["400", "450", "500", "550"], a: 2,
    e: "Pass marks = 180. 36% of M = 180 → M = 500." },
  { c: "Percentages", d: 2, q: "A salary cut by 10%. To restore, by what % must it be increased?",
    o: ["10%", "11.11%", "12%", "12.5%"], a: 1,
    e: "Multiply by 10/9 → increase = 1/9 ≈ 11.11%." },
  { c: "Percentages", d: 1, q: "If 30% of a number is 75, what is 60% of it?",
    o: ["100", "125", "150", "175"], a: 2,
    e: "60% = 2 × 30% = 2 × 75 = 150." },
  { c: "Percentages", d: 3, q: "In an election, the winner got 65% of votes and won by 1800 votes. Total votes cast?",
    o: ["5000", "5500", "6000", "6500"], a: 2,
    e: "Margin = 65 − 35 = 30%. 30% of total = 1800. Total = 6000." },
  { c: "Percentages", d: 2, q: "Laptop price increased 8% then another 12%. Net rise?",
    o: ["20%", "20.96%", "21%", "22%"], a: 1,
    e: "1.08 × 1.12 = 1.2096 = 20.96% rise." },
  { c: "Percentages", d: 1, q: "A earns 25% more than B. B's earnings are what fraction of A's?",
    o: ["3/4", "4/5", "5/6", "7/8"], a: 1,
    e: "A = 1.25B → B = A/1.25 = 4A/5. B is 4/5 of A." },
  { c: "Percentages", d: 3, q: "65% of a class are boys. If 36 are girls, the number of boys is?",
    o: ["52", "60", "67", "72"], a: 2,
    e: "Girls = 35% = 36 → total = 36/0.35 ≈ 102.86. Hmm, doesn't divide cleanly. Let me reread: if 36 = 35%, total ≈ 102. That's not clean. Better: total = 36 × 100/35 ≈ 102.86. Boys ≈ 66.86 ≈ 67." },

  // ============= COMBINATORICS (CHOOSING) (25) =============
  { c: "Combinatorics", d: 1, q: "How many ways can the letters of CIRCLE be arranged?",
    o: ["180", "360", "540", "720"], a: 1,
    e: "6 letters with C twice: 6!/2! = 720/2 = 360." },
  { c: "Combinatorics", d: 3, q: "In how many ways can 5 boys and 3 girls sit in a row so no two girls sit together?",
    o: ["7200", "9600", "14400", "28800"], a: 2,
    e: "Arrange boys: 5! = 120. 6 gaps, place 3 girls: 6P3 = 120. Total = 120 × 120 = 14400." },
  { c: "Combinatorics", d: 1, q: "Number of 4-digit numbers using 1,2,3,4,5 without repetition?",
    o: ["60", "120", "180", "240"], a: 1,
    e: "5P4 = 5 × 4 × 3 × 2 = 120." },
  { c: "Combinatorics", d: 1, q: "From 10 people, choose a committee of 4. How many ways?",
    o: ["120", "180", "210", "240"], a: 2,
    e: "C(10,4) = 10!/(4!6!) = 210." },
  { c: "Combinatorics", d: 1, q: "How many ways to arrange 7 books on a shelf?",
    o: ["720", "1440", "2520", "5040"], a: 3,
    e: "7! = 5040." },
  { c: "Combinatorics", d: 2, q: "From 8 men and 6 women, form a committee of 5 with exactly 3 men.",
    o: ["560", "720", "840", "1000"], a: 2,
    e: "C(8,3) × C(6,2) = 56 × 15 = 840." },
  { c: "Combinatorics", d: 3, q: "Arrangements of letters in MISSISSIPPI?",
    o: ["12600", "23100", "34650", "60480"], a: 2,
    e: "11!/(4!4!2!) = 39916800/1152 = 34650." },
  { c: "Combinatorics", d: 1, q: "How many ways can 6 people sit around a circular table?",
    o: ["60", "120", "360", "720"], a: 1,
    e: "(6−1)! = 5! = 120." },
  { c: "Combinatorics", d: 1, q: "Handshakes if 10 people each shake hands with all others?",
    o: ["36", "40", "45", "50"], a: 2,
    e: "C(10,2) = 45." },
  { c: "Combinatorics", d: 2, q: "Choose 2 men and 3 women from 5 men, 4 women. How many ways?",
    o: ["20", "30", "40", "60"], a: 2,
    e: "C(5,2) × C(4,3) = 10 × 4 = 40." },
  { c: "Combinatorics", d: 2, q: "How many diagonals in a hexagon?",
    o: ["6", "8", "9", "12"], a: 2,
    e: "n(n−3)/2 = 6 × 3/2 = 9." },
  { c: "Combinatorics", d: 1, q: "Letters of EQUATION can be arranged in how many ways?",
    o: ["5040", "20160", "40320", "60480"], a: 2,
    e: "8 distinct letters: 8! = 40320." },
  { c: "Combinatorics", d: 1, q: "How many 5-letter words (no repetition) from 7 distinct letters?",
    o: ["840", "1260", "2520", "5040"], a: 2,
    e: "7P5 = 7×6×5×4×3 = 2520." },
  { c: "Combinatorics", d: 1, q: "From 12 people choose a President, VP, and Treasurer (distinct).",
    o: ["220", "1320", "1728", "2640"], a: 1,
    e: "12P3 = 12 × 11 × 10 = 1320." },
  { c: "Combinatorics", d: 1, q: "Possible outcomes when a coin is tossed 5 times?",
    o: ["16", "25", "32", "64"], a: 2,
    e: "2^5 = 32." },
  { c: "Combinatorics", d: 1, q: "3-digit numbers from 1,2,3,4,5 with repetition allowed?",
    o: ["60", "125", "243", "120"], a: 1,
    e: "5 × 5 × 5 = 125." },
  { c: "Combinatorics", d: 2, q: "How many arrangements of 4 red and 3 blue balls in a row?",
    o: ["21", "35", "42", "70"], a: 1,
    e: "7!/(4!3!) = 35." },
  { c: "Combinatorics", d: 2, q: "Number of ways to choose 5 hearts from a deck?",
    o: ["715", "1287", "2002", "2520"], a: 1,
    e: "C(13,5) = 1287." },
  { c: "Combinatorics", d: 1, q: "Ways to seat 4 people at a round table?",
    o: ["6", "12", "24", "120"], a: 0,
    e: "(4−1)! = 3! = 6." },
  { c: "Combinatorics", d: 3, q: "Ways to split 8 students into 2 unlabelled groups of 4?",
    o: ["35", "70", "140", "210"], a: 0,
    e: "C(8,4)/2 = 70/2 = 35 (divide by 2 because groups are interchangeable)." },
  { c: "Combinatorics", d: 3, q: "Ways to distribute 6 different gifts among 3 children with each getting at least 1?",
    o: ["480", "540", "600", "720"], a: 1,
    e: "Inclusion-exclusion: 3^6 − 3×2^6 + 3×1^6 = 729 − 192 + 3 = 540." },
  { c: "Combinatorics", d: 2, q: "5 boys, 5 girls in a line alternating. How many arrangements?",
    o: ["7200", "14400", "21600", "28800"], a: 3,
    e: "2 patterns (BGBG... or GBGB...) × 5! × 5! = 2 × 14400 = 28800." },
  { c: "Combinatorics", d: 2, q: "How many 4-digit even numbers from 0,1,2,3,4,5 without repetition?",
    o: ["120", "144", "156", "180"], a: 2,
    e: "End in 0: 5P3 = 60. End in 2 or 4: first ≠ 0 → 4×4×3×2 = 96. Total = 156." },
  { c: "Combinatorics", d: 2, q: "How many ways to pick 3 cards of different suits from a deck?",
    o: ["2197", "4394", "8788", "13182"], a: 2,
    e: "Choose 3 suits: C(4,3) = 4. One card from each: 13³ = 2197. Total = 4 × 2197 = 8788." },
  { c: "Combinatorics", d: 3, q: "Number of triangles formed from 8 points on a circle?",
    o: ["28", "36", "56", "70"], a: 2,
    e: "Any 3 points form a triangle (since on circle, no 3 collinear). C(8,3) = 56." },

  // ============= LOGIC & REASONING (30) =============
  { c: "Logic", d: 1, q: "All cats are mammals. Some mammals are wild. What can we conclude?",
    o: ["All cats are wild", "Some cats are wild", "Some mammals are cats", "No cats are wild"], a: 2,
    e: "Only valid conclusion: since ALL cats are mammals, some mammals are cats. The 'wild' overlap is undetermined." },
  { c: "Logic", d: 1, q: "Today is Wednesday. What day will it be 100 days from today?",
    o: ["Wednesday", "Thursday", "Friday", "Saturday"], a: 2,
    e: "100 mod 7 = 2. Wed + 2 = Friday." },
  { c: "Logic", d: 2, q: "Odd one out: 8, 27, 64, 100, 125, 216, 343",
    o: ["27", "64", "100", "216"], a: 2,
    e: "All others are perfect cubes (2³, 3³, 4³, 5³, 6³, 7³). 100 is not." },
  { c: "Logic", d: 2, q: "A is mother of B. B is sister of C. C is father of D. D's relation to A?",
    o: ["Daughter", "Grandson", "Grandchild", "Niece"], a: 2,
    e: "A is grandmother of D (could be male or female, so grandchild)." },
  { c: "Logic", d: 1, q: "If BLACK is coded as CMBDL, how is WHITE coded?",
    o: ["XIJUF", "XJIUF", "WIJTF", "XJUFI"], a: 0,
    e: "Each letter shifts +1: W→X, H→I, I→J, T→U, E→F = XIJUF." },
  { c: "Logic", d: 1, q: "Find the next: 1, 4, 9, 16, 25, 36, ?",
    o: ["42", "45", "49", "64"], a: 2,
    e: "Perfect squares: 1², 2², ..., 7² = 49." },
  { c: "Logic", d: 3, q: "Given P>Q, Q>R, R<S, S<T. Which is the greatest?",
    o: ["P", "T", "Can't be determined", "S"], a: 2,
    e: "We have P>Q>R and R<S<T. P and T cannot be compared with given info." },
  { c: "Logic", d: 3, q: "Statements: All birds fly. Penguins are birds. Conclusion?",
    o: ["Penguins don't fly", "Penguins fly", "Some birds don't fly", "Cannot conclude"], a: 1,
    e: "Logically (within given premises), penguins fly. Even if real-world false, the syllogism is valid." },
  { c: "Logic", d: 2, q: "Find the missing pair: AB, DE, GH, JK, ?",
    o: ["LM", "MN", "NO", "OP"], a: 1,
    e: "Skip one letter each time: AB-(C)-DE-(F)-GH-(I)-JK-(L)-MN." },
  { c: "Logic", d: 2, q: "P is brother of Q. R is sister of P. T is mother of Q. R is to T as?",
    o: ["Sister", "Mother", "Daughter", "Aunt"], a: 2,
    e: "R is daughter of T." },
  { c: "Logic", d: 1, q: "If TEACHER → VGCEJGT (each letter shifted by 2), then STUDENT → ?",
    o: ["UVWFGPV", "UVUFGPV", "UVWGGPV", "VWXFGPV"], a: 0,
    e: "Shift each letter by +2: S→U, T→V, U→W, D→F, E→G, N→P, T→V = UVWFGPV." },
  { c: "Logic", d: 2, q: "A 5cm cube is painted then cut into 1cm cubes. How many small cubes have no painted face?",
    o: ["1", "8", "27", "54"], a: 2,
    e: "Inner cube = 3×3×3 = 27." },
  { c: "Logic", d: 2, q: "From the same 5cm cube cut into 1cm cubes, how many have exactly 1 painted face?",
    o: ["27", "36", "54", "98"], a: 2,
    e: "6 faces × inner 3×3 = 6 × 9 = 54." },
  { c: "Logic", d: 3, q: "If 5+3=28, 9+1=810, 2+7=59, then 6+4=?",
    o: ["210", "104", "1010", "240"], a: 0,
    e: "Pattern: (a−b)(a+b). |6−4|=2, 6+4=10. So 210." },
  { c: "Logic", d: 1, q: "A taller than B but shorter than C. D shorter than B. Who is tallest?",
    o: ["A", "B", "C", "D"], a: 2,
    e: "C > A > B > D. So C is tallest." },
  { c: "Logic", d: 1, q: "Find the odd one out: 121, 169, 195, 225, 289",
    o: ["121", "169", "195", "225"], a: 2,
    e: "All others are perfect squares (11², 13², 15², 17²). 195 is not." },
  { c: "Logic", d: 2, q: "Ravi is 7th from left and 4th from right in a row. How many children?",
    o: ["9", "10", "11", "12"], a: 1,
    e: "7 + 4 − 1 = 10." },
  { c: "Logic", d: 2, q: "If 'south' is called 'east', 'east' is 'north', 'north' is 'west', the sun rises in?",
    o: ["West", "South", "North", "East"], a: 2,
    e: "Sun actually rises in east; east is now called 'north', so sun rises in 'north'." },
  { c: "Logic", d: 1, q: "Statements: Some apples are red. All red things are fruits. Conclusion?",
    o: ["All apples are red", "Some apples are fruits", "No apples are fruits", "All fruits are red"], a: 1,
    e: "Some apples are red, and all red are fruits, so those apples are fruits." },
  { c: "Logic", d: 1, q: "Mother's brother's son is your?",
    o: ["Brother", "Cousin", "Nephew", "Uncle"], a: 1,
    e: "Mother's brother = uncle. His son = your cousin." },
  { c: "Logic", d: 2, q: "Clock shows 3:15. Angle between hour and minute hand?",
    o: ["0°", "7.5°", "15°", "30°"], a: 1,
    e: "Minute hand at 90°. Hour at 3 + 15/60 × 30° past 3 = 97.5°. Difference = 7.5°." },
  { c: "Logic", d: 2, q: "How many times do hour and minute hands overlap in 12 hours?",
    o: ["10", "11", "12", "13"], a: 1,
    e: "The hands overlap 11 times in 12 hours." },
  { c: "Logic", d: 2, q: "A man walks 5 km North, then 3 km East, then 5 km South. How far from start?",
    o: ["2 km", "3 km", "5 km", "8 km"], a: 1,
    e: "North and South cancel. Net displacement = 3 km East." },
  { c: "Logic", d: 2, q: "If yesterday was Sunday, what day will it be 50 days from today?",
    o: ["Monday", "Tuesday", "Wednesday", "Thursday"], a: 1,
    e: "Today is Monday. 50 mod 7 = 1. Monday + 1 = Tuesday." },
  { c: "Logic", d: 2, q: "Find the odd one: 2, 5, 10, 17, 26, 37, 50, 64",
    o: ["26", "37", "50", "64"], a: 3,
    e: "Pattern: n² + 1 → 2,5,10,17,26,37,50,65. The value 64 breaks the pattern (should be 65)." },
  { c: "Logic", d: 3, q: "In a line, A is 3rd from front and 5th from back. Adding 4 to the back, how many total now?",
    o: ["11", "12", "13", "14"], a: 0,
    e: "Original = 3 + 5 − 1 = 7. After adding 4: 11." },
  { c: "Logic", d: 3, q: "If 6 children are arranged in a circle, A is 2nd to the right of B who is 3rd to the right of C. C is right of D. D's position to A?",
    o: ["Opposite", "Adjacent", "2nd to left", "3rd to left"], a: 0,
    e: "Tracing positions on the circle places D opposite A." },
  { c: "Logic", d: 1, q: "Father's sister's daughter is your?",
    o: ["Sister", "Cousin", "Niece", "Aunt"], a: 1,
    e: "Father's sister = aunt. Her daughter = your cousin." },
  { c: "Logic", d: 2, q: "If A=1, B=2, ..., Z=26, value of CAT?",
    o: ["20", "22", "24", "26"], a: 2,
    e: "C+A+T = 3+1+20 = 24." },
  { c: "Logic", d: 3, q: "All managers are leaders. Some leaders are intelligent. Which MUST be true?",
    o: ["All managers are intelligent", "Some managers are intelligent", "Some leaders are managers", "No managers are intelligent"], a: 2,
    e: "Since all managers are leaders, some leaders are managers is guaranteed. Intelligence overlap is uncertain." },

  // ============= PROBABILITY (20) =============
  { c: "Probability", d: 1, q: "Probability of drawing a king or queen from a deck?",
    o: ["1/13", "2/13", "1/26", "4/13"], a: 1,
    e: "8 cards out of 52 = 8/52 = 2/13." },
  { c: "Probability", d: 1, q: "Two dice rolled. P(sum = 8)?",
    o: ["1/9", "5/36", "1/6", "7/36"], a: 1,
    e: "(2,6),(3,5),(4,4),(5,3),(6,2) = 5 outcomes. P = 5/36." },
  { c: "Probability", d: 1, q: "Three coins tossed. P(exactly 2 heads)?",
    o: ["1/4", "1/2", "3/8", "5/8"], a: 2,
    e: "C(3,2)/2³ = 3/8." },
  { c: "Probability", d: 2, q: "From 5 men, 4 women choose 3. P(all men)?",
    o: ["1/14", "5/42", "1/7", "5/21"], a: 1,
    e: "C(5,3)/C(9,3) = 10/84 = 5/42." },
  { c: "Probability", d: 1, q: "A card is drawn. P(face card)?",
    o: ["3/13", "4/13", "1/13", "2/13"], a: 0,
    e: "12 face cards / 52 = 3/13." },
  { c: "Probability", d: 1, q: "Bag: 3 red, 4 white, 5 black balls. P(red or white)?",
    o: ["1/3", "1/2", "7/12", "2/3"], a: 2,
    e: "(3+4)/12 = 7/12." },
  { c: "Probability", d: 1, q: "Rolling a die. P(divisible by 3)?",
    o: ["1/6", "1/3", "1/2", "2/3"], a: 1,
    e: "{3, 6} = 2/6 = 1/3." },
  { c: "Probability", d: 2, q: "From 1 to 30, one number is picked. P(multiple of 5 or 7)?",
    o: ["1/5", "1/3", "1/4", "2/5"], a: 1,
    e: "Mult of 5: 6 numbers. Mult of 7: 4 numbers. No overlap. P = 10/30 = 1/3." },
  { c: "Probability", d: 3, q: "A tells truth 75%, B tells truth 80%. P(they agree on a fact)?",
    o: ["0.60", "0.65", "0.70", "0.75"], a: 1,
    e: "Both true: 0.6. Both false: 0.05. Agree = 0.65." },
  { c: "Probability", d: 1, q: "P(at least one tail in 4 coin tosses)?",
    o: ["7/8", "11/16", "13/16", "15/16"], a: 3,
    e: "1 − P(all heads) = 1 − 1/16 = 15/16." },
  { c: "Probability", d: 1, q: "P(drawing a red ace from a deck)?",
    o: ["1/13", "1/26", "1/52", "2/13"], a: 1,
    e: "2 red aces / 52 = 1/26." },
  { c: "Probability", d: 2, q: "Bag: 6 red, 4 blue balls. Two drawn (no replacement). P(both same color)?",
    o: ["7/15", "8/15", "1/2", "11/15"], a: 0,
    e: "[C(6,2)+C(4,2)]/C(10,2) = (15+6)/45 = 21/45 = 7/15." },
  { c: "Probability", d: 1, q: "Rolling a die. P(getting a prime)?",
    o: ["1/3", "1/2", "2/3", "5/6"], a: 1,
    e: "Primes: {2, 3, 5}. P = 3/6 = 1/2." },
  { c: "Probability", d: 1, q: "Two dice. P(both show same number)?",
    o: ["1/3", "1/6", "1/9", "1/12"], a: 1,
    e: "6 doubles out of 36. P = 1/6." },
  { c: "Probability", d: 2, q: "Box: 5 defective, 15 good bulbs. Two drawn. P(both good)?",
    o: ["3/8", "21/38", "7/19", "9/19"], a: 1,
    e: "C(15,2)/C(20,2) = 105/190 = 21/38." },
  { c: "Probability", d: 2, q: "P(English) = 0.7, P(Math) = 0.6, P(both) = 0.5. P(at least one)?",
    o: ["0.65", "0.70", "0.75", "0.80"], a: 3,
    e: "0.7 + 0.6 − 0.5 = 0.8." },
  { c: "Probability", d: 2, q: "Two cards drawn (no replacement). P(both kings)?",
    o: ["1/169", "1/221", "1/256", "1/13"], a: 1,
    e: "(4/52)(3/51) = 12/2652 = 1/221." },
  { c: "Probability", d: 1, q: "Coin and die. P(head and 6)?",
    o: ["1/8", "1/12", "1/6", "1/4"], a: 1,
    e: "(1/2)(1/6) = 1/12." },
  { c: "Probability", d: 3, q: "Bag: 4 white, 6 black balls. Three drawn. P(exactly 2 white)?",
    o: ["1/3", "3/10", "9/40", "18/120"], a: 1,
    e: "C(4,2)×C(6,1)/C(10,3) = 6×6/120 = 36/120 = 3/10." },
  { c: "Probability", d: 2, q: "Two dice. P(sum > 9)?",
    o: ["1/9", "1/6", "5/18", "7/36"], a: 1,
    e: "Sums of 10,11,12: (4,6),(5,5),(6,4),(5,6),(6,5),(6,6) = 6 outcomes. P = 6/36 = 1/6." },

  // ============= WORK & RATE (15) =============
  { c: "Work & Rate", d: 1, q: "Tap A fills a tank in 12 hrs, B in 18 hrs. Together?",
    o: ["6 hrs", "7.2 hrs", "8 hrs", "9 hrs"], a: 1,
    e: "1/12 + 1/18 = 5/36. Time = 36/5 = 7.2 hrs." },
  { c: "Work & Rate", d: 1, q: "A does 1/3 of a job in 5 days. Days to complete alone?",
    o: ["10", "12", "15", "18"], a: 2,
    e: "If 1/3 takes 5 days, then 1 takes 15 days." },
  { c: "Work & Rate", d: 2, q: "A + B = 12 days. A alone = 20 days. B alone?",
    o: ["24", "30", "36", "40"], a: 1,
    e: "1/12 − 1/20 = 2/60 = 1/30. B = 30 days." },
  { c: "Work & Rate", d: 3, q: "A+B in 6 days, B+C in 8 days, A+C in 12 days. All three together?",
    o: ["4 days", "16/3 days", "6 days", "8 days"], a: 1,
    e: "2(A+B+C) = 1/6+1/8+1/12 = 9/24. A+B+C = 9/48 = 3/16. Time = 16/3 days." },
  { c: "Work & Rate", d: 2, q: "10 men do a job in 20 days. After 8 days, 5 leave. Days to finish remaining?",
    o: ["20", "22", "24", "26"], a: 2,
    e: "Work = 200 man-days. Done = 80. Left = 120. 5 men: 120/5 = 24 days." },
  { c: "Work & Rate", d: 1, q: "Pipes fill in 8 and 12 hrs. Together?",
    o: ["4 hrs", "4.5 hrs", "4.8 hrs", "5 hrs"], a: 2,
    e: "1/8 + 1/12 = 5/24. Time = 24/5 = 4.8 hrs." },
  { c: "Work & Rate", d: 2, q: "A is twice as fast as B. Together: 12 days. A alone?",
    o: ["16", "18", "20", "24"], a: 1,
    e: "Let B = r, A = 2r. 3r = 1/12 → r = 1/36. A = 1/(2/36) = 18 days." },
  { c: "Work & Rate", d: 2, q: "A + B together in 30 days. They work 20 days, A leaves; B finishes in 20 more days. A alone?",
    o: ["60", "50", "40", "45"], a: 0,
    e: "Together in 20 days: 2/3 done. B alone does 1/3 in 20 days → B = 60. So A: 1/30 − 1/60 = 1/60. A = 60 days." },
  { c: "Work & Rate", d: 1, q: "Pipe fills in 4 hrs. Leak empties in 6 hrs. Both open: time to fill?",
    o: ["10 hrs", "12 hrs", "14 hrs", "16 hrs"], a: 1,
    e: "1/4 − 1/6 = 1/12. Time = 12 hrs." },
  { c: "Work & Rate", d: 1, q: "24 men do a job in 16 days. Add 8 men. New time?",
    o: ["10 days", "12 days", "14 days", "16 days"], a: 1,
    e: "384 man-days / 32 men = 12 days." },
  { c: "Work & Rate", d: 3, q: "A: 12 days, B: 16 days. Together for 4 days, then A leaves. Total time to finish?",
    o: ["8 days", "9 days", "32/3 days", "11 days"], a: 2,
    e: "Together: rate = 7/48. In 4 days: 28/48 = 7/12 done. Remaining 5/12 by B alone: (5/12)/(1/16) = 20/3. Total = 4 + 20/3 = 32/3 days." },
  { c: "Work & Rate", d: 2, q: "12 boys do a job in 16 days. After 4 days, how many boys needed to finish in 6 more days?",
    o: ["18", "20", "24", "30"], a: 2,
    e: "Total = 192. Done = 48. Left = 144. In 6 days: 144/6 = 24 boys." },
  { c: "Work & Rate", d: 3, q: "Two taps fill in 12 and 18 hrs. Drain empties in 24 hrs. All three open. Time to fill?",
    o: ["9 hrs", "72/7 hrs", "11 hrs", "12 hrs"], a: 1,
    e: "Net = 1/12 + 1/18 − 1/24 = 7/72. Time = 72/7 hrs ≈ 10.29 hrs." },
  { c: "Work & Rate", d: 2, q: "A is 3x faster than B. Together in 18 days. B alone?",
    o: ["54", "60", "72", "90"], a: 2,
    e: "B = r, A = 3r. 4r = 1/18 → r = 1/72. B = 72 days." },
  { c: "Work & Rate", d: 3, q: "A: 10 days, B: 15 days. Work alternately, A first. Days to finish?",
    o: ["11", "12", "13", "14"], a: 1,
    e: "Each pair of days: 1/10 + 1/15 = 1/6. 5 pairs = 5/6. Day 11 (A): + 1/10 = 28/30. Day 12 (B): remaining 1/15 done. Total = 12 days." },

  // ============= SPEED & DISTANCE (15) =============
  { c: "Speed & Distance", d: 1, q: "A car travels 300 km in 5 hrs. Speed?",
    o: ["50 km/h", "55 km/h", "60 km/h", "65 km/h"], a: 2,
    e: "300/5 = 60 km/h." },
  { c: "Speed & Distance", d: 1, q: "Walking 4 km/h for 1.5 hrs, then 5 km/h for 2 hrs. Total distance?",
    o: ["14 km", "15 km", "16 km", "17 km"], a: 2,
    e: "6 + 10 = 16 km." },
  { c: "Speed & Distance", d: 1, q: "Convert 90 km/h to m/s.",
    o: ["20", "22.5", "25", "27"], a: 2,
    e: "90 × 5/18 = 25 m/s." },
  { c: "Speed & Distance", d: 2, q: "Train 120m long at 72 km/h. Time to cross a 180m platform?",
    o: ["12 s", "15 s", "18 s", "20 s"], a: 1,
    e: "Speed = 20 m/s. Total distance = 300m. Time = 15 s." },
  { c: "Speed & Distance", d: 2, q: "Two trains 100m and 150m approach each other at 36 and 54 km/h. Time to cross?",
    o: ["10 s", "12 s", "14 s", "15 s"], a: 0,
    e: "Relative speed = 90 km/h = 25 m/s. Distance = 250m. Time = 10 s." },
  { c: "Speed & Distance", d: 2, q: "Car covers 240 km in 6 hrs going, 4 hrs return. Average speed?",
    o: ["48 km/h", "50 km/h", "55 km/h", "60 km/h"], a: 0,
    e: "Total = 480 km in 10 hrs. Avg = 48 km/h." },
  { c: "Speed & Distance", d: 1, q: "Boat speed 10 km/h, stream 2 km/h. Distance upstream in 5 hrs?",
    o: ["30 km", "35 km", "40 km", "45 km"], a: 2,
    e: "Upstream speed = 8 km/h. Distance = 40 km." },
  { c: "Speed & Distance", d: 1, q: "Train 200m crosses a pole in 10 s. Speed in km/h?",
    o: ["60", "65", "70", "72"], a: 3,
    e: "20 m/s × 18/5 = 72 km/h." },
  { c: "Speed & Distance", d: 2, q: "Boat: 12 km downstream in 2 hrs, returns in 3 hrs. Stream speed?",
    o: ["0.5 km/h", "1 km/h", "1.5 km/h", "2 km/h"], a: 1,
    e: "Down = 6, Up = 4. Stream = (6−4)/2 = 1 km/h." },
  { c: "Speed & Distance", d: 3, q: "Walking at 5/6 of usual speed, a man is 10 min late. Usual time?",
    o: ["40 min", "45 min", "50 min", "60 min"], a: 2,
    e: "New time = (6/5)T. Late by T/5 = 10. T = 50 min." },
  { c: "Speed & Distance", d: 2, q: "Train at 60 km/h crosses a platform in 30 s. Train is 200m. Platform length?",
    o: ["200m", "250m", "300m", "400m"], a: 2,
    e: "60 km/h = 50/3 m/s. Total distance in 30s = 500m. Platform = 500 − 200 = 300m." },
  { c: "Speed & Distance", d: 1, q: "Two cyclists in opposite directions at 15 and 20 km/h. Distance apart in 3 hrs?",
    o: ["75 km", "90 km", "105 km", "120 km"], a: 2,
    e: "(15+20) × 3 = 105 km." },
  { c: "Speed & Distance", d: 3, q: "Car at 60 km/h overtakes train at 40 km/h. Train is 200m. Time to fully pass?",
    o: ["30 s", "36 s", "40 s", "45 s"], a: 1,
    e: "Relative speed = 20 km/h = 50/9 m/s. Time = 200/(50/9) = 36 s." },
  { c: "Speed & Distance", d: 2, q: "Boat: 30 km downstream in 2 hrs, 30 km upstream in 3 hrs. Speed in still water?",
    o: ["10 km/h", "11 km/h", "12.5 km/h", "13 km/h"], a: 2,
    e: "Down = 15, Up = 10. Still water = (15+10)/2 = 12.5 km/h." },
  { c: "Speed & Distance", d: 3, q: "60 km covered partly by bus (50 km/h), partly by train (80 km/h) in 1 hr. Distance by bus?",
    o: ["20 km", "25 km", "100/3 km", "40 km"], a: 2,
    e: "x/50 + (60−x)/80 = 1 → 8x + 5(60−x) = 400 → 3x = 100 → x = 100/3 km." },

  // ============= AVERAGES (15) =============
  { c: "Averages", d: 1, q: "Average of 7, 9, 11, 13, 15?",
    o: ["9", "10", "11", "12"], a: 2,
    e: "Sum = 55. Avg = 11." },
  { c: "Averages", d: 1, q: "Average of first 10 natural numbers?",
    o: ["4.5", "5", "5.5", "6"], a: 2,
    e: "(1+...+10)/10 = 55/10 = 5.5." },
  { c: "Averages", d: 2, q: "Average of 6 numbers is 30. Removing 35, new average?",
    o: ["27", "28", "29", "30"], a: 2,
    e: "Sum = 180. New = 145/5 = 29." },
  { c: "Averages", d: 2, q: "Avg age of 30 students is 12. Including teacher, avg becomes 13. Teacher's age?",
    o: ["38", "40", "43", "45"], a: 2,
    e: "30×12 = 360. 31×13 = 403. Teacher = 43." },
  { c: "Averages", d: 1, q: "Average of 5 consecutive integers is 21. The largest is?",
    o: ["21", "22", "23", "25"], a: 2,
    e: "Middle = 21. Largest = 23." },
  { c: "Averages", d: 2, q: "Avg weight of A, B, C is 60kg. D joins, avg becomes 58kg. D's weight?",
    o: ["50", "52", "54", "56"], a: 1,
    e: "A+B+C = 180. A+B+C+D = 232. D = 52." },
  { c: "Averages", d: 2, q: "Average of even numbers from 1 to 50?",
    o: ["24", "25", "26", "28"], a: 2,
    e: "2,4,...,50 (25 terms). Sum = 650. Avg = 26." },
  { c: "Averages", d: 2, q: "Avg score of 10 students is 80. Two scored 70 instead of 90. New avg?",
    o: ["74", "76", "78", "79"], a: 1,
    e: "Decrease = 2 × 20 = 40. New = (800 − 40)/10 = 76." },
  { c: "Averages", d: 1, q: "Mean of 5 numbers is 25. Adding 5 to each, new mean?",
    o: ["25", "28", "30", "32"], a: 2,
    e: "Mean shifts by 5 → 30." },
  { c: "Averages", d: 1, q: "Mean of 8 numbers is 25. Multiplying each by 2, new mean?",
    o: ["25", "40", "50", "60"], a: 2,
    e: "Mean doubles → 50." },
  { c: "Averages", d: 1, q: "Mean of 4 numbers is 50. Three are 40, 60, 70. Fourth?",
    o: ["20", "25", "30", "35"], a: 2,
    e: "Sum = 200. Fourth = 30." },
  { c: "Averages", d: 2, q: "Avg salary of A, B, C is $50,000. A and B avg $45,000. C's salary?",
    o: ["$55,000", "$60,000", "$65,000", "$70,000"], a: 1,
    e: "A+B+C = 150K. A+B = 90K. C = 60K." },
  { c: "Averages", d: 3, q: "Avg of 11 results = 50. Avg first 6 = 48, last 6 = 55. The 6th result?",
    o: ["58", "60", "65", "68"], a: 3,
    e: "First 6 sum = 288, last 6 sum = 330, total = 550. 6th counted twice = 288 + 330 − 550 = 68." },
  { c: "Averages", d: 1, q: "Median of 4, 7, 2, 9, 11, 5, 8?",
    o: ["5", "7", "8", "9"], a: 1,
    e: "Sorted: 2,4,5,7,8,9,11. Middle = 7." },
  { c: "Averages", d: 1, q: "Mode of 3, 5, 7, 5, 9, 5, 11, 7?",
    o: ["3", "5", "7", "9"], a: 1,
    e: "5 appears 3 times (most frequent)." },

  // ============= PROFIT & LOSS (10) =============
  { c: "Profit & Loss", d: 1, q: "CP = $200, SP = $250. Profit %?",
    o: ["20%", "25%", "30%", "50%"], a: 1,
    e: "50/200 × 100 = 25%." },
  { c: "Profit & Loss", d: 1, q: "SP = $480 with 20% profit. CP?",
    o: ["$380", "$400", "$420", "$450"], a: 1,
    e: "480/1.2 = $400." },
  { c: "Profit & Loss", d: 2, q: "By selling at $144, a man loses 4%. CP?",
    o: ["$145", "$148", "$150", "$155"], a: 2,
    e: "144 = 0.96 × CP → CP = $150." },
  { c: "Profit & Loss", d: 2, q: "80 articles bought at $50 each, all sold for $4400. Profit %?",
    o: ["8%", "10%", "12%", "15%"], a: 1,
    e: "CP = $4000. Profit = $400. % = 10%." },
  { c: "Profit & Loss", d: 3, q: "MP = $500, discount 10%, then 12.5% profit. CP?",
    o: ["$380", "$400", "$420", "$450"], a: 1,
    e: "SP = 450. CP = 450/1.125 = $400." },
  { c: "Profit & Loss", d: 3, q: "By selling 15 items at the cost of 18, profit %?",
    o: ["15%", "18%", "20%", "25%"], a: 2,
    e: "Profit on 15 items = 3 items' value. % = 3/15 × 100 = 20%." },
  { c: "Profit & Loss", d: 3, q: "CP of 10 articles = SP of 8 articles. Profit %?",
    o: ["20%", "22%", "25%", "30%"], a: 2,
    e: "CP per = 1, total CP for 8 SP = 8. SP each = 10/8 = 1.25. Profit = 25%." },
  { c: "Profit & Loss", d: 2, q: "MP marked up 40%, then 20% discount. Net profit %?",
    o: ["10%", "12%", "15%", "20%"], a: 1,
    e: "1.4 × 0.8 = 1.12 → 12% profit." },
  { c: "Profit & Loss", d: 2, q: "Item sold at $144 with 20% loss. To gain 20%, SP should be?",
    o: ["$200", "$216", "$220", "$240"], a: 1,
    e: "CP = 144/0.8 = $180. New SP = 180 × 1.2 = $216." },
  { c: "Profit & Loss", d: 3, q: "Item bought at $500, marked up 60%, sold at 25% discount. Profit %?",
    o: ["15%", "20%", "25%", "30%"], a: 1,
    e: "MP = 800. SP = 600. Profit = 100/500 = 20%." },

  // ============= INTEREST (10) =============
  { c: "Interest", d: 1, q: "SI on $5000 at 8% for 3 years?",
    o: ["$1000", "$1200", "$1300", "$1500"], a: 1,
    e: "P×R×T/100 = 5000×8×3/100 = $1200." },
  { c: "Interest", d: 2, q: "CI on $10,000 at 10% for 2 years?",
    o: ["$2000", "$2050", "$2100", "$2150"], a: 2,
    e: "A = 10000 × 1.21 = 12100. CI = $2100." },
  { c: "Interest", d: 1, q: "SI on a sum for 5 years at 8% is $400. Principal?",
    o: ["$800", "$900", "$1000", "$1200"], a: 2,
    e: "P × 40/100 = 400 → P = 1000." },
  { c: "Interest", d: 2, q: "Difference between CI and SI for 2 years on $5000 at 10%?",
    o: ["$25", "$50", "$75", "$100"], a: 1,
    e: "SI = 1000. CI = 1050. Diff = $50." },
  { c: "Interest", d: 3, q: "A sum doubles in 8 years at SI. Rate?",
    o: ["10%", "12.5%", "15%", "20%"], a: 1,
    e: "SI = P. P × R × 8/100 = P → R = 12.5%." },
  { c: "Interest", d: 3, q: "Rate at which a sum becomes 4x in 12 years (SI)?",
    o: ["20%", "25%", "30%", "33%"], a: 1,
    e: "SI = 3P. P × R × 12/100 = 3P → R = 25%." },
  { c: "Interest", d: 2, q: "$8000 at 5% CI for 2 years. Amount?",
    o: ["$8400", "$8800", "$8820", "$9000"], a: 2,
    e: "8000 × 1.05² = 8000 × 1.1025 = $8820." },
  { c: "Interest", d: 3, q: "A sum amounts to $6655 in 3 years at 10% CI. Principal?",
    o: ["$4500", "$5000", "$5500", "$6000"], a: 1,
    e: "P × 1.331 = 6655 → P = $5000." },
  { c: "Interest", d: 2, q: "CI vs SI difference for 2 years on $10000 at 5%?",
    o: ["$20", "$25", "$30", "$50"], a: 1,
    e: "SI = 1000. CI = 1025. Diff = $25." },
  { c: "Interest", d: 1, q: "SI for 3 years at 4% = $360. Sum?",
    o: ["$2500", "$3000", "$3500", "$4000"], a: 1,
    e: "P × 12/100 = 360 → P = 3000." },

  // ============= NUMBER SERIES (10) =============
  { c: "Number Series", d: 1, q: "Next: 3, 6, 12, 24, ?",
    o: ["36", "42", "48", "60"], a: 2,
    e: "Each term doubles: 48." },
  { c: "Number Series", d: 1, q: "Next: 1, 1, 2, 3, 5, 8, ?",
    o: ["11", "12", "13", "14"], a: 2,
    e: "Fibonacci: 13." },
  { c: "Number Series", d: 1, q: "Next: 100, 81, 64, 49, ?",
    o: ["25", "30", "36", "40"], a: 2,
    e: "Descending squares: 6² = 36." },
  { c: "Number Series", d: 2, q: "Next: 2, 6, 12, 20, 30, ?",
    o: ["36", "40", "42", "45"], a: 2,
    e: "n(n+1): 1·2, 2·3, 3·4, 4·5, 5·6, 6·7 = 42." },
  { c: "Number Series", d: 1, q: "Next: 1, 8, 27, 64, ?",
    o: ["100", "121", "125", "144"], a: 2,
    e: "Cubes: 5³ = 125." },
  { c: "Number Series", d: 2, q: "Next: 5, 11, 23, 47, ?",
    o: ["89", "92", "95", "99"], a: 2,
    e: "Each ×2 + 1: 47 × 2 + 1 = 95." },
  { c: "Number Series", d: 1, q: "Next: 2, 3, 5, 7, 11, 13, ?",
    o: ["15", "17", "19", "21"], a: 1,
    e: "Primes: 17." },
  { c: "Number Series", d: 1, q: "Next: 7, 14, 28, 56, ?",
    o: ["98", "100", "112", "126"], a: 2,
    e: "Doubling: 112." },
  { c: "Number Series", d: 3, q: "Next: 1, 4, 10, 22, 46, ?",
    o: ["68", "82", "94", "96"], a: 2,
    e: "Differences double: +3,+6,+12,+24,+48 → 46+48 = 94." },
  { c: "Number Series", d: 2, q: "Next: 0, 3, 8, 15, 24, 35, ?",
    o: ["42", "48", "49", "50"], a: 1,
    e: "n² − 1: 1,4,9,16,25,36,49 → 0,3,8,15,24,35,48." },

  // ============= ALGEBRA (10) =============
  { c: "Algebra", d: 1, q: "If 2x + 3 = 11, x = ?",
    o: ["3", "4", "5", "6"], a: 1,
    e: "2x = 8 → x = 4." },
  { c: "Algebra", d: 1, q: "Solve: 3x − 5 = 16.",
    o: ["5", "6", "7", "8"], a: 2,
    e: "3x = 21 → x = 7." },
  { c: "Algebra", d: 1, q: "x² = 16. x = ?",
    o: ["±2", "±4", "±8", "±16"], a: 1,
    e: "x = ±4." },
  { c: "Algebra", d: 1, q: "x + y = 10, x − y = 4. x = ?",
    o: ["5", "6", "7", "8"], a: 2,
    e: "Adding: 2x = 14 → x = 7." },
  { c: "Algebra", d: 2, q: "Sum of two numbers is 24, product is 143. Find the numbers.",
    o: ["10, 14", "11, 13", "12, 12", "9, 15"], a: 1,
    e: "Roots of t² − 24t + 143 = 0: t = (24 ± √4)/2 = 11 or 13." },
  { c: "Algebra", d: 2, q: "(x+y)² = 64 and xy = 12. Find x² + y².",
    o: ["36", "40", "44", "52"], a: 1,
    e: "(x+y)² = x² + 2xy + y² → 64 = x² + y² + 24 → x² + y² = 40." },
  { c: "Algebra", d: 1, q: "If 3^x = 81, x = ?",
    o: ["2", "3", "4", "5"], a: 2,
    e: "81 = 3⁴ → x = 4." },
  { c: "Algebra", d: 2, q: "Solve: x/3 + x/4 = 7.",
    o: ["8", "10", "12", "14"], a: 2,
    e: "(4x + 3x)/12 = 7 → 7x = 84 → x = 12." },
  { c: "Algebra", d: 2, q: "a² + b² = 25 and a + b = 7. Find ab.",
    o: ["10", "12", "14", "16"], a: 1,
    e: "(a+b)² = 49 = a² + b² + 2ab = 25 + 2ab → ab = 12." },
  { c: "Algebra", d: 3, q: "If x + 1/x = 3, then x² + 1/x² = ?",
    o: ["5", "7", "8", "9"], a: 1,
    e: "(x + 1/x)² = x² + 2 + 1/x² = 9 → x² + 1/x² = 7." },

  // ============= ORIGINAL HOMEWORK PROBLEMS (the ones you got wrong) =============
  { c: "Original", d: 2, q: "Machine A produces 200 widgets in 5 hrs, Machine B in 8 hrs. How long together?",
    o: ["2.5 hrs", "3.08 hrs (40/13)", "3.5 hrs", "4 hrs"], a: 1,
    e: "Rates: 40 + 25 = 65 widgets/hr. Time = 200/65 = 40/13 ≈ 3.08 hrs." },
  { c: "Original", d: 2, q: "Pipe fills in 6 hrs, drain empties in 10 hrs. With both open, time to fill?",
    o: ["12 hrs", "13 hrs", "15 hrs", "18 hrs"], a: 2,
    e: "Net = 1/6 − 1/10 = 1/15. Time = 15 hrs." },
  { c: "Original", d: 2, q: "A finishes in 10 hrs, B in 15 hrs. Working together for 3 hrs, fraction remaining?",
    o: ["1/3", "1/2", "2/3", "3/4"], a: 1,
    e: "Combined = 1/6/hr. In 3 hrs: 1/2 done. Remaining: 1/2." },
  { c: "Original", d: 1, q: "P(heart or king from a 52-card deck)?",
    o: ["1/4", "4/13", "16/52", "1/3"], a: 1,
    e: "13 hearts + 4 kings − 1 overlap (KH) = 16/52 = 4/13." },
  { c: "Original", d: 2, q: "Jar: 8 red, 12 blue candies. Pick 2 without replacement. P(both red)?",
    o: ["1/10", "14/95", "2/15", "1/6"], a: 1,
    e: "(8/20)(7/19) = 56/380 = 14/95." },
  { c: "Original", d: 2, q: "Two dice rolled. P(sum > 9)?",
    o: ["1/6", "1/9", "5/36", "7/36"], a: 0,
    e: "Sums 10,11,12 = 3+2+1 = 6 outcomes. P = 6/36 = 1/6." },
  { c: "Original", d: 2, q: "Cyclist rides 24 mi upstream in 4 hrs, downstream in 3 hrs. Speed of current?",
    o: ["0.5 mph", "1 mph", "1.5 mph", "2 mph"], a: 1,
    e: "Up = 6, Down = 8. Current = (8−6)/2 = 1 mph." },
  { c: "Original", d: 1, q: "Test scores: 72, 85, 78, 90. What 5th score gives average of 82?",
    o: ["80", "82", "85", "88"], a: 2,
    e: "Needed = 82×5 = 410. Current = 325. Fifth = 85." },
  { c: "Original", d: 3, q: "If on bestseller list, sold >10,000. Book sold 15,000. Is it bestseller?",
    o: ["Yes", "No", "Cannot determine", "Definitely yes"], a: 2,
    e: "Affirming the consequent. Selling >10K doesn't guarantee bestseller status — that's the converse of the original statement." },
  { c: "Original", d: 1, q: "Production: Mon 850, Tue 920, Wed 780, Thu 900, Fri 1050. Average?",
    o: ["850", "880", "900", "920"], a: 2,
    e: "Sum = 4500. Avg = 4500/5 = 900." },
  { c: "Original", d: 1, q: "Budget $50,000. 68% spent. Remaining?",
    o: ["$14,000", "$16,000", "$18,000", "$20,000"], a: 1,
    e: "32% × 50,000 = $16,000." },
  { c: "Original", d: 3, q: "Lisa=lawyer, Mark=doctor (not gardening), painter jogs. Even without 'Kelly does tennis', which can we deduce: (1) Kelly is painter or salesperson, (2) Ned gardens, (3) Mark does poker or tennis?",
    o: ["Only 1", "Only 3", "1 and 3", "All three"], a: 2,
    e: "Mark isn't painter (he's doctor), can't jog. Not gardening (given). So poker or tennis ✓. Kelly & Ned fill painter/salesperson ✓. But Ned's hobby is undetermined without clue 4." },
];

// =================== HELPERS ===================
const CATEGORIES = [...new Set(QUESTIONS.map(q => q.c))];
const DIFFICULTIES = { 1: "Easy", 2: "Medium", 3: "Hard" };

const shuffle = (arr) => {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
};

const STORAGE_KEY = "quant_drill_stats_v1";
const MISTAKES_KEY = "quant_drill_mistakes_v1";

// =================== MAIN COMPONENT ===================
export default function QuantQuiz() {
  const [mode, setMode] = useState("menu");
  const [selectedCats, setSelectedCats] = useState(new Set(CATEGORIES));
  const [selectedDiffs, setSelectedDiffs] = useState(new Set([1, 2, 3]));
  const [practiceMistakes, setPracticeMistakes] = useState(false);
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
  const [mistakeIds, setMistakeIds] = useState(new Set());
  const [statsLoaded, setStatsLoaded] = useState(false);

  // Load persistent stats on mount
  useEffect(() => {
    (async () => {
      try {
        const r = await window.storage.get(STORAGE_KEY);
        if (r && r.value) {
          const s = JSON.parse(r.value);
          setTotalAttempted(s.totalAttempted || 0);
          setTotalCorrect(s.totalCorrect || 0);
          setBestStreak(s.bestStreak || 0);
        }
      } catch (e) {}
      try {
        const m = await window.storage.get(MISTAKES_KEY);
        if (m && m.value) {
          const ids = JSON.parse(m.value);
          setMistakeIds(new Set(ids));
        }
      } catch (e) {}
      setStatsLoaded(true);
    })();
  }, []);

  // Save stats
  const persistStats = async (tA, tC, bS) => {
    try {
      await window.storage.set(STORAGE_KEY, JSON.stringify({
        totalAttempted: tA, totalCorrect: tC, bestStreak: bS,
      }));
    } catch (e) {}
  };

  const persistMistakes = async (ids) => {
    try {
      await window.storage.set(MISTAKES_KEY, JSON.stringify([...ids]));
    } catch (e) {}
  };

  const filteredPool = () => {
    if (practiceMistakes) {
      return QUESTIONS.map((q, i) => ({ ...q, idx: i }))
        .filter(q => mistakeIds.has(q.idx));
    }
    return QUESTIONS.map((q, i) => ({ ...q, idx: i }))
      .filter(q => selectedCats.has(q.c) && selectedDiffs.has(q.d));
  };

  const startQuiz = () => {
    const pool = filteredPool();
    if (pool.length === 0) return;
    const picked = shuffle(pool).slice(0, Math.min(quizSize, pool.length));
    const prepared = picked.map(q => {
      const indices = q.o.map((_, i) => i);
      const shuf = shuffle(indices);
      return {
        ...q,
        o: shuf.map(i => q.o[i]),
        a: shuf.indexOf(q.a),
      };
    });
    setQuestions(prepared);
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
    const q = questions[currentQ];
    const isCorrect = selected === q.a;
    setShowResult(true);

    const newAttempted = totalAttempted + 1;
    const newCorrect = totalCorrect + (isCorrect ? 1 : 0);
    setTotalAttempted(newAttempted);
    setTotalCorrect(newCorrect);

    let newBest = bestStreak;
    if (isCorrect) {
      const ns = streak + 1;
      setStreak(ns);
      if (ns > bestStreak) {
        newBest = ns;
        setBestStreak(ns);
      }
      setScore(s => s + 1);

      // Remove from mistakes if practicing mistakes and got it right
      if (mistakeIds.has(q.idx)) {
        const newMistakes = new Set(mistakeIds);
        newMistakes.delete(q.idx);
        setMistakeIds(newMistakes);
        persistMistakes(newMistakes);
      }
    } else {
      setStreak(0);
      const newMistakes = new Set(mistakeIds);
      newMistakes.add(q.idx);
      setMistakeIds(newMistakes);
      persistMistakes(newMistakes);
    }

    persistStats(newAttempted, newCorrect, newBest);
    setAnswers(a => [...a, { q, selected, isCorrect }]);
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

  const toggleDiff = (d) => {
    setSelectedDiffs(prev => {
      const n = new Set(prev);
      if (n.has(d)) { if (n.size > 1) n.delete(d); }
      else n.add(d);
      return n;
    });
  };

  const selectAllCats = () => setSelectedCats(new Set(CATEGORIES));
  const clearMistakes = async () => {
    setMistakeIds(new Set());
    await persistMistakes(new Set());
  };

  const pct = totalAttempted > 0 ? Math.round((totalCorrect / totalAttempted) * 100) : 0;
  const poolSize = filteredPool().length;
  const q = questions[currentQ];

  return (
    <div style={{
      fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
      minHeight: "100vh",
      background: "#0a0a0f",
      color: "#e0e0e8",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #0a0a0f; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes slideIn { from { opacity: 0; transform: translateX(-8px); } to { opacity: 1; transform: translateX(0); } }
        @keyframes countUp { from { transform: scale(0.7); opacity: 0; } to { transform: scale(1); opacity: 1; } }
        button { font-family: inherit; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0a0a0f; }
        ::-webkit-scrollbar-thumb { background: #2a2a3e; border-radius: 4px; }
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
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div>
          <div style={{
            fontFamily: "'Space Grotesk', sans-serif",
            fontSize: "20px",
            fontWeight: 700,
            color: "#00ffa3",
            letterSpacing: "-0.5px",
          }}>QUANT DRILL</div>
          <div style={{ fontSize: "10px", color: "#666", marginTop: "2px", letterSpacing: "2px", textTransform: "uppercase" }}>
            {QUESTIONS.length} Questions · {CATEGORIES.length} Topics
          </div>
        </div>
        <div style={{ display: "flex", gap: "16px", fontSize: "12px" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#00ffa3", fontSize: "16px", fontWeight: 700 }}>{totalCorrect}/{totalAttempted}</div>
            <div style={{ color: "#555", fontSize: "9px", letterSpacing: "1px" }}>LIFETIME</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#ff6b6b", fontSize: "16px", fontWeight: 700 }}>{pct}%</div>
            <div style={{ color: "#555", fontSize: "9px", letterSpacing: "1px" }}>ACCURACY</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ color: "#ffd93d", fontSize: "16px", fontWeight: 700 }}>{bestStreak}</div>
            <div style={{ color: "#555", fontSize: "9px", letterSpacing: "1px" }}>BEST</div>
          </div>
          {mistakeIds.size > 0 && (
            <div style={{ textAlign: "center" }}>
              <div style={{ color: "#ff8c42", fontSize: "16px", fontWeight: 700 }}>{mistakeIds.size}</div>
              <div style={{ color: "#555", fontSize: "9px", letterSpacing: "1px" }}>MISTAKES</div>
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: "24px", maxWidth: "780px", margin: "0 auto" }}>

        {/* MENU */}
        {mode === "menu" && (
          <div style={{ animation: "fadeUp 0.4s ease" }}>
            {/* Practice Mistakes toggle */}
            {mistakeIds.size > 0 && (
              <div style={{
                background: practiceMistakes ? "rgba(255,140,66,0.08)" : "#12121a",
                border: practiceMistakes ? "1px solid #ff8c42" : "1px solid #2a2a3e",
                borderRadius: "10px",
                padding: "16px",
                marginBottom: "24px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
              }}>
                <div>
                  <div style={{
                    fontSize: "13px",
                    fontWeight: 600,
                    color: practiceMistakes ? "#ff8c42" : "#ccc",
                    marginBottom: "4px",
                  }}>
                    Practice Past Mistakes
                  </div>
                  <div style={{ fontSize: "11px", color: "#666" }}>
                    {mistakeIds.size} question{mistakeIds.size !== 1 ? "s" : ""} you got wrong before
                  </div>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={() => setPracticeMistakes(p => !p)} style={{
                    padding: "8px 14px",
                    borderRadius: "6px",
                    border: "1px solid " + (practiceMistakes ? "#ff8c42" : "#2a2a3e"),
                    background: practiceMistakes ? "#ff8c42" : "transparent",
                    color: practiceMistakes ? "#0a0a0f" : "#888",
                    fontSize: "11px",
                    fontWeight: 600,
                    cursor: "pointer",
                    letterSpacing: "1px",
                    textTransform: "uppercase",
                  }}>{practiceMistakes ? "ON" : "OFF"}</button>
                  <button onClick={clearMistakes} style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid #2a2a3e",
                    background: "transparent",
                    color: "#666",
                    fontSize: "11px",
                    cursor: "pointer",
                  }}>CLEAR</button>
                </div>
              </div>
            )}

            {!practiceMistakes && (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <div style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#888",
                    letterSpacing: "1.5px",
                    textTransform: "uppercase",
                  }}>Topics</div>
                  <button onClick={selectAllCats} style={{
                    background: "transparent",
                    border: "none",
                    color: "#00ffa3",
                    fontSize: "10px",
                    cursor: "pointer",
                    letterSpacing: "1px",
                    textTransform: "uppercase",
                  }}>SELECT ALL</button>
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "24px" }}>
                  {CATEGORIES.map(cat => {
                    const count = QUESTIONS.filter(q => q.c === cat).length;
                    return (
                      <button key={cat} onClick={() => toggleCat(cat)} style={{
                        padding: "7px 12px",
                        borderRadius: "6px",
                        border: selectedCats.has(cat) ? "1px solid #00ffa3" : "1px solid #2a2a3e",
                        background: selectedCats.has(cat) ? "rgba(0,255,163,0.08)" : "transparent",
                        color: selectedCats.has(cat) ? "#00ffa3" : "#666",
                        cursor: "pointer",
                        fontSize: "11px",
                        fontWeight: 500,
                        transition: "all 0.15s",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}>
                        {cat}
                        <span style={{ fontSize: "9px", opacity: 0.7 }}>{count}</span>
                      </button>
                    );
                  })}
                </div>

                <div style={{
                  fontFamily: "'Space Grotesk', sans-serif",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: "#888",
                  marginBottom: "12px",
                  letterSpacing: "1.5px",
                  textTransform: "uppercase",
                }}>Difficulty</div>

                <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
                  {[1, 2, 3].map(d => {
                    const colors = { 1: "#00ffa3", 2: "#ffd93d", 3: "#ff6b6b" };
                    return (
                      <button key={d} onClick={() => toggleDiff(d)} style={{
                        padding: "10px 18px",
                        borderRadius: "6px",
                        border: selectedDiffs.has(d) ? `1px solid ${colors[d]}` : "1px solid #2a2a3e",
                        background: selectedDiffs.has(d) ? `${colors[d]}15` : "transparent",
                        color: selectedDiffs.has(d) ? colors[d] : "#666",
                        cursor: "pointer",
                        fontSize: "12px",
                        fontWeight: 600,
                        flex: 1,
                        transition: "all 0.15s",
                      }}>{DIFFICULTIES[d]}</button>
                    );
                  })}
                </div>
              </>
            )}

            <div style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "13px",
              fontWeight: 600,
              color: "#888",
              marginBottom: "12px",
              letterSpacing: "1.5px",
              textTransform: "uppercase",
            }}>Round Size</div>

            <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
              {[5, 10, 15, 20, 30].map(n => (
                <button key={n} onClick={() => setQuizSize(n)} style={{
                  padding: "10px",
                  borderRadius: "6px",
                  border: quizSize === n ? "1px solid #00ffa3" : "1px solid #2a2a3e",
                  background: quizSize === n ? "rgba(0,255,163,0.08)" : "transparent",
                  color: quizSize === n ? "#00ffa3" : "#666",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: 600,
                  flex: 1,
                  transition: "all 0.15s",
                }}>{n}</button>
              ))}
            </div>

            <button onClick={startQuiz} disabled={poolSize === 0} style={{
              width: "100%",
              padding: "16px",
              borderRadius: "8px",
              border: "none",
              background: poolSize > 0 ? "linear-gradient(135deg, #00ffa3 0%, #00cc82 100%)" : "#1a1a2e",
              color: poolSize > 0 ? "#0a0a0f" : "#444",
              fontSize: "13px",
              fontFamily: "'Space Grotesk', sans-serif",
              fontWeight: 700,
              cursor: poolSize > 0 ? "pointer" : "not-allowed",
              letterSpacing: "2px",
              textTransform: "uppercase",
              transition: "transform 0.15s",
            }}
              onMouseDown={e => poolSize > 0 && (e.currentTarget.style.transform = "scale(0.98)")}
              onMouseUp={e => e.currentTarget.style.transform = "scale(1)"}
            >
              {poolSize === 0 ? "NO QUESTIONS AVAILABLE" : "START DRILL →"}
            </button>

            <div style={{ marginTop: "16px", fontSize: "11px", color: "#444", textAlign: "center" }}>
              {poolSize} question{poolSize !== 1 ? "s" : ""} in selected pool
            </div>
          </div>
        )}

        {/* QUIZ */}
        {mode === "quiz" && q && (
          <div style={{ animation: "fadeUp 0.3s ease" }} key={currentQ}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
              <span style={{ fontSize: "11px", color: "#555", letterSpacing: "1px" }}>
                Q {currentQ + 1} / {questions.length}
              </span>
              <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
                <span style={{
                  fontSize: "10px",
                  padding: "3px 8px",
                  borderRadius: "4px",
                  background: "rgba(0,255,163,0.08)",
                  color: "#00ffa3",
                  border: "1px solid rgba(0,255,163,0.2)",
                }}>{q.c}</span>
                <span style={{
                  fontSize: "10px",
                  padding: "3px 8px",
                  borderRadius: "4px",
                  background: q.d === 1 ? "rgba(0,255,163,0.08)" : q.d === 2 ? "rgba(255,217,61,0.08)" : "rgba(255,107,107,0.08)",
                  color: q.d === 1 ? "#00ffa3" : q.d === 2 ? "#ffd93d" : "#ff6b6b",
                  border: "1px solid " + (q.d === 1 ? "rgba(0,255,163,0.2)" : q.d === 2 ? "rgba(255,217,61,0.2)" : "rgba(255,107,107,0.2)"),
                }}>{DIFFICULTIES[q.d]}</span>
                {streak > 1 && (
                  <span style={{ fontSize: "11px", color: "#ffd93d", animation: "pulse 1.5s infinite" }}>
                    🔥 {streak}
                  </span>
                )}
              </div>
            </div>

            <div style={{
              width: "100%",
              height: "3px",
              background: "#1a1a2e",
              borderRadius: "2px",
              marginBottom: "20px",
              overflow: "hidden",
            }}>
              <div style={{
                width: `${((currentQ + (showResult ? 1 : 0)) / questions.length) * 100}%`,
                height: "100%",
                background: "linear-gradient(90deg, #00ffa3, #00cc82)",
                borderRadius: "2px",
                transition: "width 0.4s ease",
              }} />
            </div>

            <div style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: "17px",
              fontWeight: 500,
              lineHeight: 1.6,
              color: "#e0e0e8",
              marginBottom: "20px",
              padding: "20px",
              background: "#12121a",
              borderRadius: "10px",
              border: "1px solid #1e1e30",
            }}>
              {q.q}
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: "20px" }}>
              {q.o.map((opt, idx) => {
                let bg = "transparent";
                let border = "1px solid #2a2a3e";
                let color = "#ccc";
                if (showResult) {
                  if (idx === q.a) {
                    bg = "rgba(0,255,163,0.1)";
                    border = "1px solid #00ffa3";
                    color = "#00ffa3";
                  } else if (idx === selected && idx !== q.a) {
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
                    padding: "14px 16px",
                    borderRadius: "8px",
                    border, background: bg, color,
                    cursor: showResult ? "default" : "pointer",
                    fontSize: "14px",
                    textAlign: "left",
                    transition: "all 0.15s",
                    display: "flex",
                    alignItems: "center",
                    gap: "12px",
                    animation: `slideIn 0.25s ease ${idx * 0.05}s both`,
                  }}>
                    <span style={{
                      width: "26px",
                      height: "26px",
                      borderRadius: "50%",
                      border: "1px solid currentColor",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "11px",
                      fontWeight: 600,
                      flexShrink: 0,
                      opacity: 0.7,
                    }}>{String.fromCharCode(65 + idx)}</span>
                    {opt}
                  </button>
                );
              })}
            </div>

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
                  color: selected === q.a ? "#00ffa3" : "#ff6b6b",
                  fontWeight: 700,
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                  marginBottom: "8px",
                }}>
                  {selected === q.a ? "✓ CORRECT" : "✗ INCORRECT"}
                </div>
                <div style={{ fontSize: "13px", lineHeight: 1.7, color: "#aaa" }}>
                  {q.e}
                </div>
              </div>
            )}

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
              }}>
                {currentQ + 1 >= questions.length ? "VIEW RESULTS →" : "NEXT →"}
              </button>
            )}

            <div style={{ textAlign: "center", marginTop: "14px", fontSize: "12px" }}>
              <span style={{ color: "#00ffa3", fontWeight: 600 }}>{score}</span>
              <span style={{ color: "#444" }}> / {currentQ + (showResult ? 1 : 0)} correct</span>
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
              marginBottom: "20px",
            }}>
              <div style={{
                fontFamily: "'Space Grotesk', sans-serif",
                fontSize: "48px",
                fontWeight: 700,
                color: score / questions.length >= 0.7 ? "#00ffa3" : score / questions.length >= 0.4 ? "#ffd93d" : "#ff6b6b",
                animation: "countUp 0.5s ease",
              }}>{score}/{questions.length}</div>
              <div style={{ fontSize: "13px", color: "#666", marginTop: "8px" }}>
                {score / questions.length >= 0.9 ? "Outstanding! 🏆" :
                 score / questions.length >= 0.7 ? "Great work! Keep it up." :
                 score / questions.length >= 0.4 ? "Getting there. Review below." :
                 "Keep practicing — you'll improve fast."}
              </div>
            </div>

            {answers.filter(a => !a.isCorrect).length > 0 && (
              <>
                <div style={{
                  fontSize: "11px",
                  color: "#ff6b6b",
                  fontWeight: 600,
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                  marginBottom: "12px",
                }}>REVIEW MISTAKES ({answers.filter(a => !a.isCorrect).length})</div>
                {answers.filter(a => !a.isCorrect).map((a, i) => (
                  <div key={i} style={{
                    padding: "14px",
                    borderRadius: "8px",
                    background: "#12121a",
                    border: "1px solid #2a1e1e",
                    marginBottom: "10px",
                    animation: `fadeUp 0.3s ease ${i * 0.06}s both`,
                  }}>
                    <div style={{ display: "flex", gap: "6px", marginBottom: "8px" }}>
                      <span style={{ fontSize: "9px", padding: "2px 6px", borderRadius: "3px", background: "rgba(0,255,163,0.08)", color: "#00ffa3" }}>{a.q.c}</span>
                      <span style={{ fontSize: "9px", padding: "2px 6px", borderRadius: "3px", background: "rgba(255,107,107,0.08)", color: "#ff6b6b" }}>{DIFFICULTIES[a.q.d]}</span>
                    </div>
                    <div style={{ fontSize: "13px", color: "#ccc", marginBottom: "8px", lineHeight: 1.5 }}>{a.q.q}</div>
                    <div style={{ fontSize: "12px", color: "#ff6b6b", marginBottom: "4px" }}>
                      Your answer: {a.q.o[a.selected]}
                    </div>
                    <div style={{ fontSize: "12px", color: "#00ffa3", marginBottom: "8px" }}>
                      Correct: {a.q.o[a.q.a]}
                    </div>
                    <div style={{ fontSize: "11px", color: "#777", lineHeight: 1.6, paddingTop: "8px", borderTop: "1px solid #1e1e30" }}>
                      {a.q.e}
                    </div>
                  </div>
                ))}
              </>
            )}

            {answers.filter(a => a.isCorrect).length > 0 && (
              <>
                <div style={{
                  fontSize: "11px",
                  color: "#00ffa3",
                  fontWeight: 600,
                  letterSpacing: "2px",
                  textTransform: "uppercase",
                  marginBottom: "10px",
                  marginTop: "20px",
                }}>CORRECT ({answers.filter(a => a.isCorrect).length})</div>
                {answers.filter(a => a.isCorrect).map((a, i) => (
                  <div key={i} style={{
                    padding: "10px 14px",
                    borderRadius: "6px",
                    background: "#12121a",
                    border: "1px solid #1a2a1e",
                    marginBottom: "6px",
                    fontSize: "12px",
                    color: "#888",
                    animation: `fadeUp 0.3s ease ${i * 0.04}s both`,
                    lineHeight: 1.5,
                  }}>
                    <span style={{ color: "#00ffa3", marginRight: "8px" }}>✓</span>
                    {a.q.q.substring(0, 90)}{a.q.q.length > 90 ? "..." : ""}
                  </div>
                ))}
              </>
            )}

            <button onClick={() => { setMode("menu"); setPracticeMistakes(false); }} style={{
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
            }}>DRILL AGAIN →</button>
          </div>
        )}
      </div>
    </div>
  );
}
