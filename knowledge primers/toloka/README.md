# Toloka Forward Deployed AI Engineer: the final-round book

A 67-page preparation book for the final-round interview for Toloka's freelance **Forward Deployed AI Engineer** role: a conversational interview with the Head of Technical Consultants built around two practical use cases, judged on approach, structure, questions, communication and technical decisions. The book covers what Toloka sells, the LLM post-training knowledge the interviewer probes, how human-data engagements are run and priced, how to work a client live, and the author's own stories and questions.

## Files

| File | What it is |
|---|---|
| `Toloka Forward Deployed AI Engineer - The Final-Round Book.md` | The book in Markdown, with the two diagrams linked from `images/` |
| `Toloka Forward Deployed AI Engineer - The Final-Round Book.pdf` | The same document as a 67-page US-letter PDF |
| `images/llm-training-pipeline.png` | The six-stage LLM training pipeline and where Toloka's products sit |
| `images/toloka-data-factory.png` | A data engagement as a factory: four phases, the rework loop, the roles |
| `scoping-and-pricing-playbook.html` | Interactive scoping & pricing playbook (open in a browser): one card per product line — preference annotation, reasoning data, robotics video, coding environments, agentic gyms — each with discovery questions, metrics, non-functional requirements, a dataset record, system design, a pipeline diagram and illustrative pricing; plus a consultative script (discovery, BLUF, talking price, objections, red flags), an agentic-systems reference (τ-bench, Terminal-Bench, SWE-bench Verified, pass@k vs pass^k) and an LLM-as-a-judge setup for annotation QA with every metric's formula |

## Contents

**Part I — Toloka and the role.** 1. What Toloka does (experts, crowd and platform; the product families from SFT and preference data to agent environments, trajectories, red-teaming and Arena; the Quality Loop; the 2025 investment). 2. The role, decoded. 3. The final interview and a table of the interviewer's common questions.

**Part II — The LLM knowledge the interviewer will probe.** 4. How LLMs are trained and what data each stage needs. 5. Data for post-training: a product catalogue with JSONL schemas. 6. Evaluation data and what quality alignment means. 7. Code: LoRA SFT, DPO, reward-model and GRPO training with TRL, and an RLAIF loop.

**Part III — How Toloka builds data.** 8. The data factory. 9. Quality control: Cohen's kappa, Krippendorff's alpha, Dawid–Skene, skill scores, golden sets. 10. Pipelines and tooling, including a toloka-kit pool configuration. 11. Commercial ownership: margin, levers and checkpoints with a worked unit-economics example.

**Part IV — Working the client.** 12. Discovery: the question behind the question (a seven-question script). 13. Executive communication (BLUF). 14. Two practical use cases worked end to end, plus a safety variant.

**Part V — Me in the room.** 15. STAR stories mapped to what is being assessed. 16. Questions to ask, the closing line, the night-before and in-interview checklists. Appendix: glossary and sources.

## How it was built

Written on 17 October 2026 as a Claude Doc from Toloka's public pages and blog, the press coverage of its 2025 investment, the job description and the recruiter's brief, the author's resume and cover letter for the role, and the standard post-training literature (InstructGPT, DPO, GRPO, Constitutional AI, LoRA, Dawid–Skene, Krippendorff). Sections 1 and 2 carry the figures that age; appendix A.3 says what to re-check the morning of the interview.
