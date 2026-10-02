# LLM Fine-Tuning: A Complete Practical Guide

Prepared for interview preparation and real system design. Updated May 2026.

This guide explains fine-tuning from first principles, then moves into modern production practice: supervised fine-tuning, instruction tuning, LoRA/QLoRA, preference optimization, RLHF, reinforcement fine-tuning, data design, training, evaluation, deployment, and common failure modes.

## 1. The One-Sentence Definition

Fine-tuning means taking a model that already knows a lot and training it further on examples that teach it a narrower behavior.

Simple version:

```text
Pretraining teaches a model language and broad world patterns.
Fine-tuning teaches it how you want it to behave for a specific task.
```

Fine-tuning does not usually teach a model a large new private knowledge base. It is better at teaching:

- style
- format
- task behavior
- domain language
- decision boundaries
- tool-use patterns
- reasoning habits, when trained carefully
- preference alignment

For large changing facts, use RAG. For stable behavior, use fine-tuning.

## 2. The Mental Model

Imagine a model as a very skilled generalist.

Prompting is like giving instructions at runtime:

```text
"For this task, answer in JSON and be concise."
```

Fine-tuning is like practice:

```text
Here are 5,000 examples of how good answers look.
Adjust yourself so this behavior becomes natural.
```

That is the key intuition:

```text
Prompting = telling.
Fine-tuning = training by examples.
```

Fine-tuning changes model weights or adds trainable adapter weights. After fine-tuning, the model is more likely to produce the desired behavior even with shorter prompts.

## 3. What Fine-Tuning Is Not

Fine-tuning is often misunderstood.

It is not:

- a magic way to upload documents into the model
- a replacement for RAG when facts change often
- a guarantee of factual correctness
- a substitute for evaluation
- a cure for bad prompts, bad data, or unclear product requirements
- always better than prompting
- always cheaper, once training and maintenance are counted

Fine-tuning works best when the desired behavior is repeated, stable, and learnable from examples.

## 4. The Training Stack: Where Fine-Tuning Fits

Modern LLM development often has these stages:

```text
1. Pretraining
2. Continued pretraining / domain-adaptive pretraining
3. Supervised fine-tuning
4. Preference alignment
5. Reinforcement fine-tuning / RL for reasoning
6. Evaluation and deployment
```

You do not always need every stage.

### 4.1 Pretraining

Pretraining trains a model on massive text/code/multimodal data to predict the next token.

Objective:

```text
Given previous tokens, predict the next token.
```

Example:

```text
Input: "The capital of France is"
Target: " Paris"
```

Pretraining gives the model broad capabilities:

- grammar
- facts
- concepts
- reasoning patterns
- code patterns
- multilingual behavior
- general task priors

Most teams do not pretrain from scratch. It is extremely expensive.

### 4.2 Continued Pretraining

Continued pretraining trains the base model further on domain text using the same next-token objective.

Also called:

- domain-adaptive pretraining
- DAPT
- continual pretraining
- further pretraining

Use it when:

- the domain language is very specialized
- the model lacks vocabulary or concepts
- you have large amounts of raw domain text
- you want broad domain adaptation before instruction tuning

Examples:

- biomedical papers
- legal corpora
- financial filings
- codebase-specific source code
- internal technical documentation

Risk:

- catastrophic forgetting if overdone
- expensive
- may degrade general instruction following

### 4.3 Supervised Fine-Tuning

Supervised fine-tuning, or SFT, trains on input-output examples.

```text
Input: user request
Target: ideal assistant response
```

Use it to teach:

- response format
- tone
- task completion
- classification behavior
- extraction behavior
- domain-specific answer style
- tool-call formatting

SFT is the most common fine-tuning method.

### 4.4 Instruction Tuning

Instruction tuning is SFT where examples are phrased as instructions.

Example:

```json
{
  "instruction": "Extract the invoice number and total.",
  "input": "Invoice #A-1029. Total due: $483.20.",
  "output": {
    "invoice_number": "A-1029",
    "total": 483.20
  }
}
```

Instruction tuning teaches a model to follow user instructions across tasks, not just complete raw text.

### 4.5 Preference Alignment

Preference alignment trains from comparisons:

```text
Prompt
  -> chosen response
  -> rejected response
```

The model learns that one answer is better than another.

Methods include:

- RLHF with reward model + PPO
- DPO
- IPO
- KTO
- ORPO
- SimPO

Use it when:

- "good" is easier to judge than write
- tone/style/helpfulness needs refinement
- SFT answers are correct but not preferred
- you want fewer refusals, better summaries, or better response tradeoffs

### 4.6 Reinforcement Fine-Tuning

Reinforcement fine-tuning trains from reward signals rather than fixed answers.

Modern reasoning-oriented training often uses:

- verifiable rewards
- code test pass/fail
- math answer checking
- expert graders
- rubric-based rewards
- group-relative policy methods such as GRPO

Use it when:

- there are many valid solution paths
- final correctness can be automatically or expertly graded
- you want better reasoning/search behavior
- SFT demonstrations are hard to write exhaustively

## 5. The Decision: Prompting, RAG, Fine-Tuning, Or RL?

Use this table first.

| Problem | Best First Move |
| --- | --- |
| Model ignores a simple instruction | Better prompt |
| Need current/private facts | RAG |
| Need exact citations | RAG + citation validation |
| Need consistent JSON format | Structured outputs; maybe SFT |
| Need consistent tone/style | SFT or DPO |
| Need domain-specific wording | SFT or continued pretraining + SFT |
| Need to reduce prompt length/cost | SFT |
| Need many examples beyond context window | SFT |
| Need to imitate expert decisions | SFT, then DPO if preferences matter |
| Need "better than demonstrations" reasoning | RL/RFT/RLVR |
| Need tool-call syntax | Prompting + structured outputs; maybe SFT |
| Need stable behavior on repeated workflow | SFT |
| Need knowledge that changes weekly | RAG, not fine-tuning |

Good rule:

```text
Prompt first.
Evaluate.
Add RAG if facts are missing.
Fine-tune if behavior remains inconsistent.
Use preference/RL methods when examples are not enough.
```

## 6. Taxonomy Of Fine-Tuning Methods

| Method | Trains On | Changes | Best For |
| --- | --- | --- | --- |
| Full fine-tuning | input-output examples | all model weights | highest control, expensive |
| LoRA | input-output examples | low-rank adapter matrices | efficient open-model tuning |
| QLoRA | input-output examples | LoRA adapters on quantized base | low-memory tuning |
| Adapters | input-output examples | small inserted modules | modular task adapters |
| Prefix/prompt tuning | examples | trainable prefix vectors | very parameter-efficient |
| SFT | ideal responses | model or adapters | task/style/format behavior |
| Instruction tuning | instruction-response examples | model or adapters | general instruction following |
| DPO | chosen/rejected pairs | model or adapters | preference alignment without reward model |
| ORPO | instruction + preference-style data | model or adapters | SFT + preference in one objective |
| KTO | desirable/undesirable examples | model or adapters | alignment without paired comparisons |
| SimPO | chosen/rejected pairs | model or adapters | reference-free preference tuning |
| RLHF/PPO | reward model feedback | model policy | classic alignment pipeline |
| RFT/RLVR/GRPO | reward function or grader | model policy | reasoning, math, code, expert tasks |
| Distillation | teacher outputs | student model | smaller/faster model imitation |

## 7. Full Fine-Tuning

Full fine-tuning updates all model weights.

```text
base model weights -> train all weights -> fine-tuned model
```

Pros:

- maximum flexibility
- can adapt deeply
- no adapter merge complexity

Cons:

- expensive memory and compute
- higher risk of overfitting
- higher risk of catastrophic forgetting
- one full copy per fine-tune
- harder to serve many variants

Use full fine-tuning when:

- you have strong infrastructure
- data volume is high
- behavior change is deep
- PEFT is not enough
- you are training a smaller model where full tuning is affordable

Avoid it as a first move for most teams.

## 8. Parameter-Efficient Fine-Tuning

Parameter-efficient fine-tuning, or PEFT, freezes most model weights and trains a small number of extra parameters.

Why:

- cheaper
- faster
- lower memory
- easier to store multiple task variants
- often close to full fine-tuning quality

### 8.1 LoRA

LoRA stands for Low-Rank Adaptation.

Instead of changing a large weight matrix directly, LoRA adds a small low-rank update:

```text
Original layer:
  y = W x

LoRA layer:
  y = W x + B A x
```

Where:

- `W` is frozen
- `A` and `B` are small trainable matrices
- rank `r` controls adapter capacity

Intuition:

```text
Do not rewrite the whole book.
Add a small set of correction notes in the margins.
```

Important LoRA knobs:

| Knob | Meaning |
| --- | --- |
| `r` | rank; higher means more capacity and more trainable parameters |
| `alpha` | scaling factor for LoRA update |
| `dropout` | regularization on adapter training |
| target modules | which layers receive adapters, often attention and MLP projections |
| learning rate | usually higher than full fine-tuning |

Typical ranks:

- `r=8` or `16` for small behavior changes
- `r=32` or `64` for harder adaptation
- higher ranks when domain shift is large

### 8.2 QLoRA

QLoRA combines:

- quantized base model, often 4-bit
- LoRA adapters trained on top
- memory-saving optimizer tricks

Intuition:

```text
Keep the huge base model compressed.
Train small high-precision adapter weights.
```

Why QLoRA matters:

- makes large model fine-tuning possible on limited GPUs
- strong quality for the cost
- popular for open-source model adaptation

Tradeoff:

- slower than pure full-precision in some setups
- more engineering complexity
- quantization can introduce subtle instability

### 8.3 Adapters

Adapters insert small trainable modules into model layers.

Pros:

- modular
- can swap task adapters
- base model stays frozen

Cons:

- may add inference latency if not merged
- less universally used than LoRA in LLM practice

### 8.4 Prefix And Prompt Tuning

These train virtual tokens or prefix vectors rather than model weights.

Pros:

- extremely parameter efficient
- useful for small adaptations

Cons:

- less powerful for complex behavior
- can be sensitive to setup
- often less popular than LoRA for modern LLM fine-tuning

## 9. Supervised Fine-Tuning In Detail

SFT trains the model to imitate ideal responses.

### 9.1 Dataset Shape

For chat models:

```json
{
  "messages": [
    {"role": "system", "content": "You are a concise support assistant."},
    {"role": "user", "content": "How do I reset my password?"},
    {"role": "assistant", "content": "Go to Settings > Security > Reset password, then follow the email link."}
  ]
}
```

For instruction models:

```json
{
  "instruction": "Classify the support ticket.",
  "input": "My card was charged twice.",
  "output": "billing_issue"
}
```

For extraction:

```json
{
  "input": "Invoice A-1029 total due $483.20 due June 2.",
  "output": {
    "invoice_id": "A-1029",
    "total_due": 483.20,
    "due_date": "2026-06-02"
  }
}
```

### 9.2 Loss Function

Most SFT uses next-token cross-entropy loss.

The model predicts the assistant output token by token. Training penalizes the model when the target token has low probability.

Simplified:

```text
loss = -log probability(model assigns to correct next token)
```

During chat SFT, you usually mask loss on the prompt/user tokens and train only on the assistant response.

Why mask prompt tokens?

- you do not want the model to learn to generate the user's question
- you want it to learn the answer behavior

### 9.3 What SFT Learns Well

SFT is good for:

- formatting
- classification
- extraction
- concise response style
- domain-specific phrasing
- tool-call structure
- following recurring business rules
- imitating expert examples

SFT is weaker for:

- learning a huge fact database
- making stale knowledge current
- improving deep reasoning from shallow examples
- safety alignment without negative examples
- fixing retrieval failures

### 9.4 Data Quality Beats Data Volume

Bad fine-tuning data teaches bad behavior permanently.

High-quality examples should be:

- realistic
- diverse
- correctly labeled
- representative of production
- consistent in style and policy
- free of accidental secrets
- balanced across categories
- not contaminated with evaluation examples

The model learns patterns, including your mistakes.

## 10. Instruction Tuning

Instruction tuning is SFT over many tasks written as natural instructions.

Why it works:

- the model sees many ways users ask for things
- it learns the "instruction -> useful answer" mapping
- it generalizes better to unseen instructions

Example instruction-tuning mixture:

```text
summarization
classification
translation
question answering
extraction
rewriting
reasoning
format conversion
```

Instruction tuning is how base models become usable assistant models.

Important distinction:

```text
Base model: predicts text continuation.
Instruction-tuned model: follows user instructions.
```

## 11. Preference Tuning

SFT teaches "copy this answer."

Preference tuning teaches "prefer this kind of answer over that one."

### 11.1 Preference Data

Common format:

```json
{
  "prompt": "Summarize this customer complaint.",
  "chosen": "The customer reports being charged twice and asks for a refund.",
  "rejected": "The customer is unhappy about something related to billing."
}
```

The chosen answer is better, but the rejected answer may not be completely wrong. That makes preference tuning useful for quality gradients.

### 11.2 RLHF

Classic RLHF has three stages:

```text
1. SFT on demonstrations
2. Train reward model on human preferences
3. Optimize model with RL, often PPO, against reward model
```

Why:

- humans can often compare answers more easily than write perfect answers
- reward model provides scalable feedback
- RL optimizes the policy toward preferred behavior

Challenges:

- complex pipeline
- reward hacking
- instability
- expensive human preference data
- reward model can be wrong

### 11.3 DPO

DPO, Direct Preference Optimization, skips the explicit reward model.

It trains directly on chosen/rejected pairs.

Intuition:

```text
Increase probability of chosen response.
Decrease probability of rejected response.
Stay close enough to the reference model.
```

Why DPO became popular:

- simpler than RLHF
- stable
- no reward model training
- works well for many alignment tasks

Use DPO when you have paired preference examples.

### 11.4 ORPO

ORPO combines supervised learning and preference alignment in one objective.

It encourages the chosen answer while penalizing the rejected style.

Why people use it:

- no separate reference model
- simpler training stage
- useful when you want SFT and preference alignment together

### 11.5 KTO

KTO uses binary desirable/undesirable examples rather than paired comparisons.

Example:

```json
{
  "prompt": "...",
  "response": "...",
  "label": "desirable"
}
```

Why:

- paired preference data can be expensive
- thumbs-up/thumbs-down style data is easier to collect

Use KTO when you have unpaired positive/negative feedback.

### 11.6 SimPO

SimPO is a simpler reference-free preference optimization method.

Why it matters:

- reduces complexity
- aligns sequence-level reward more directly with generated response likelihood
- often competitive with DPO in reported benchmarks

### 11.7 When Preference Tuning Helps

Use preference tuning when:

- answers are technically correct but not preferred
- model is too verbose
- model misses tone
- summaries focus on wrong details
- model refuses too often or too little
- you need tradeoffs between helpfulness and caution
- you can collect comparisons or ratings

## 12. Reinforcement Fine-Tuning And Reasoning Training

Reasoning fine-tuning has become more important since 2024-2026.

The key idea:

```text
Do not only imitate reasoning traces.
Reward outputs that solve the problem.
```

### 12.1 RL With Verifiable Rewards

RLVR means reinforcement learning with verifiable rewards.

Useful when answers can be checked:

- math final answer
- code passes tests
- theorem/proof checker passes
- SQL query returns expected result
- extraction matches schema and ground truth
- medical/legal expert rubric produces score

Example:

```text
Prompt: solve math problem
Model samples 8 solutions
Reward: 1 if final answer correct, 0 otherwise
Training increases probability of successful solution patterns
```

### 12.2 GRPO

GRPO, Group Relative Policy Optimization, compares a group of sampled outputs for the same prompt and updates the model based on relative rewards.

Intuition:

```text
Generate several attempts.
Score them.
Make better-than-group-average attempts more likely.
Make worse-than-group-average attempts less likely.
```

Why it is useful:

- avoids a separate critic model
- fits reasoning tasks where many sampled solutions can be graded
- became prominent in reasoning-model training discussions after DeepSeekMath and DeepSeek-R1

### 12.3 Reinforcement Fine-Tuning In Hosted APIs

Hosted RFT systems let you define a grader and train a reasoning model toward higher-scored outputs.

Best for:

- expert tasks
- legal passage selection
- medical reasoning
- scientific rubric scoring
- complex classification with explanations
- specialized reasoning where output quality can be graded

Hard part:

- designing a reliable grader
- avoiding reward hacking
- making sure improvements generalize

### 12.4 SFT vs RL For Reasoning

SFT teaches the model to imitate provided solutions.

RL teaches the model to search for solutions that earn reward.

Use SFT when:

- expert demonstrations are available
- answer style matters
- task is mostly procedural

Use RL/RFT when:

- final answer can be checked
- there are many possible reasoning paths
- you want the model to improve exploration
- demonstrations are hard to enumerate

## 13. Fine-Tuning Data Design

Fine-tuning is mostly data work.

The model is the visible part. The dataset is the real product.

### 13.1 Start With A Behavior Spec

Before collecting data, write:

```text
The model should...
The model should not...
Inputs look like...
Outputs must include...
Edge cases include...
Failure is defined as...
```

Example:

```text
Task: classify customer tickets.
Labels: billing_issue, login_issue, cancellation, bug_report, other.
The model must return exactly one label.
If multiple labels apply, choose the main user intent.
Do not explain unless asked.
```

### 13.2 Build The Dataset From Real Inputs

Good sources:

- production logs
- support tickets
- expert-written examples
- eval failure cases
- synthetic examples reviewed by humans
- old prompt outputs corrected by experts
- domain-specific edge cases

Avoid:

- toy examples only
- duplicated examples
- examples that leak test data
- inconsistent labels
- giant documents as answers
- private data without governance

### 13.3 Data Splits

Use:

```text
training set: teaches the model
validation set: tunes hyperparameters and catches overfitting
test set: final unbiased measurement
```

Do not tune repeatedly on the test set.

Typical split:

```text
80% train
10% validation
10% test
```

For small data, manually construct a high-quality test set.

### 13.4 Data Size

Rough guidance:

| Use Case | Starting Examples |
| --- | --- |
| format/style adjustment | 50-300 |
| classification | 200-2,000 |
| extraction | 500-5,000 |
| support response style | 500-5,000 |
| domain assistant SFT | 2,000-50,000 |
| preference tuning | 1,000-50,000 comparisons |
| reasoning RL/RFT | depends heavily on grader and task |

Quality and coverage matter more than raw count.

### 13.5 Data Mixture

If you train only on narrow examples, the model may forget broader behavior.

A good mixture may include:

- task-specific examples
- hard edge cases
- refusal examples
- safety examples
- formatting examples
- general instruction-following examples
- negative examples for preference tuning

For open-model SFT, teams sometimes mix in general chat/instruction data to preserve broad helpfulness.

### 13.6 Synthetic Data

Synthetic data can help, but it needs filtering.

Good use:

- generate variations
- cover rare edge cases
- bootstrap low-resource tasks
- produce candidate examples for expert review

Risk:

- synthetic style becomes repetitive
- teacher model errors become training data
- model learns superficial patterns
- diversity is lower than it looks

Best practice:

```text
Generate synthetic data.
Filter for quality and diversity.
Human-review important slices.
Evaluate on real data.
```

## 14. Formatting Training Data

The training format must match inference.

If production uses chat messages, train with chat messages.

If production uses tool calls, train with tool-call examples.

If production needs JSON, train with valid JSON outputs.

### 14.1 Chat Template

Every chat model has a chat template, a way of converting role messages into tokens.

Example conceptual template:

```text
<system>
You are helpful.
<user>
Question here
<assistant>
Answer here
```

Why it matters:

- wrong template can ruin training
- model may learn wrong role boundaries
- assistant loss masking depends on template

### 14.2 Packing

Packing combines multiple short examples into one sequence to improve training efficiency.

Risk:

- if boundaries are wrong, the model learns examples bleeding into each other
- for chat data, packing must preserve conversation boundaries

### 14.3 Truncation

If examples exceed context length, they are truncated.

This can silently destroy training.

Check:

- max sequence length
- truncation side
- how many examples are cut
- whether assistant answers are truncated

### 14.4 Label Masking

For chat SFT, train on assistant tokens, not user tokens.

Conceptual mask:

```text
system tokens: ignored
user tokens: ignored
assistant tokens: loss computed
```

This teaches the model to answer, not to simulate the user.

## 15. Training Hyperparameters

Important knobs:

| Hyperparameter | Meaning |
| --- | --- |
| learning rate | step size for updates |
| batch size | number of examples per optimization step |
| epochs | passes over the dataset |
| max sequence length | token length per example |
| weight decay | regularization |
| warmup ratio | gradual LR increase at start |
| scheduler | how LR changes over time |
| gradient accumulation | simulates larger batch on limited GPU |
| gradient clipping | prevents unstable large updates |
| LoRA rank | adapter capacity |
| LoRA alpha | LoRA update scaling |
| dropout | regularization |

### 15.1 Learning Rate

Too high:

- training unstable
- model forgets general behavior
- outputs degrade

Too low:

- slow learning
- underfitting

Typical rough ranges:

- full fine-tuning: lower LR
- LoRA/QLoRA: higher LR
- small datasets: lower LR and fewer epochs
- large datasets: more stable tuning

### 15.2 Epochs

Too many epochs cause memorization and overfitting.

Watch:

```text
training loss decreases
validation loss stops improving or increases
eval quality gets worse
```

For small datasets, 1-3 epochs may be enough.

### 15.3 Batch Size

Larger batch:

- smoother gradients
- more memory

Smaller batch:

- noisier
- less memory

Use gradient accumulation when GPU memory is limited.

### 15.4 Sequence Length

Longer sequence length:

- handles longer examples
- uses more memory
- slower training

Do not set max length blindly. Inspect length distribution first.

## 16. Evaluation

Fine-tuning without evals is gambling.

### 16.1 Always Build A Baseline

Compare:

```text
base model + prompt
base model + better prompt
RAG if relevant
fine-tuned model
fine-tuned model + shorter prompt
```

Fine-tuning must beat a strong prompt baseline.

### 16.2 Evaluation Types

| Eval Type | Use |
| --- | --- |
| exact match | labels, extraction, deterministic answers |
| semantic similarity | paraphrased answers |
| human grading | style, usefulness, domain judgment |
| LLM-as-judge | scalable rubric scoring |
| pairwise preference | compare base vs fine-tuned |
| safety eval | harmful outputs, policy violations |
| regression eval | prevent old failures returning |
| latency/cost eval | production viability |

### 16.3 What To Measure

Measure:

- accuracy
- format validity
- refusal accuracy
- hallucination rate
- domain correctness
- preference win rate
- latency
- cost
- safety
- calibration
- robustness on edge cases

### 16.4 Overfitting Signals

Signs:

- train loss down, validation loss up
- model repeats training phrases
- model becomes less general
- model overuses one format
- model memorizes names or secrets
- model performs well on easy examples but fails new cases

Fixes:

- reduce epochs
- lower learning rate
- add regularization
- improve data diversity
- remove duplicates
- mix in general instruction data
- use smaller LoRA rank

## 17. Deployment

### 17.1 Hosted Fine-Tuning

Hosted APIs manage:

- training infrastructure
- model storage
- serving
- checkpointing
- basic job management

You provide:

- data
- method
- model
- evals
- safety checks

Pros:

- simple
- reliable
- no GPU management

Cons:

- less control
- model choices limited
- data governance constraints
- ongoing provider cost

### 17.2 Open-Weights Fine-Tuning

You manage:

- model choice
- tokenizer
- training framework
- GPUs
- storage
- serving
- quantization
- adapters
- evaluation

Pros:

- full control
- local/private deployment
- model portability
- more method flexibility

Cons:

- more engineering
- GPU complexity
- serving complexity
- safety burden

### 17.3 Serving LoRA Adapters

Options:

- load base model + adapter at inference
- merge adapter into base weights
- serve multiple adapters on one base model

Tradeoffs:

```text
Unmerged adapter:
  flexible, swappable, possible overhead

Merged adapter:
  simpler inference, less flexible
```

### 17.4 Quantization For Serving

Quantization reduces memory and often speeds inference.

Common:

- 8-bit
- 4-bit
- GPTQ/AWQ-style post-training quantization

Risk:

- quality drop
- tool-call/JSON instability
- domain-specific errors

Always evaluate after quantization.

## 18. Safety, Privacy, And Governance

Fine-tuning data may contain:

- PII
- secrets
- customer messages
- proprietary code
- medical/legal/financial data
- copyrighted material

Before training:

- remove secrets
- redact PII where possible
- confirm usage rights
- document data provenance
- separate train/validation/test
- restrict access
- keep audit logs
- define retention policy

After training:

- test memorization
- test prompt extraction attacks
- test safety regressions
- monitor outputs

Fine-tuned models can memorize rare strings, especially if repeated.

## 19. Common Fine-Tuning Failure Modes

| Failure | Symptom | Cause | Fix |
| --- | --- | --- | --- |
| No improvement | Fine-tune equals base | weak data, already solved by prompt | better data, harder eval |
| Overfitting | great train, poor test | too many epochs, duplicate data | reduce epochs, dedupe |
| Catastrophic forgetting | model loses general ability | too aggressive tuning | lower LR, mix data, PEFT |
| Format drift | JSON invalid | training data inconsistent | enforce schema, clean examples |
| Style overfit | same phrase every answer | repetitive data | diversify outputs |
| Hallucination remains | unsupported facts | task needs RAG/evidence | add RAG, grounding eval |
| Safety regression | more harmful answers | missing safety data | safety mix, preference tuning |
| Refusal imbalance | refuses too much/little | bad examples or labels | targeted refusal data |
| Tool-call mistakes | wrong args/schema | poor tool examples | structured outputs + more tool data |
| Memorization | outputs training secrets | sensitive repeated data | redact, dedupe, test |
| Reward hacking | high reward, bad answer | flawed grader | improve reward model/grader |

## 20. Practical Fine-Tuning Workflow

### Step 1: Define The Task

Write:

```text
What should the model do?
What inputs will it see?
What should output look like?
What is unacceptable?
How will we measure success?
```

### Step 2: Build Evals First

Create:

- representative test set
- edge cases
- safety cases
- format checks
- human or LLM judge rubric

### Step 3: Establish Baselines

Try:

- base model
- better prompt
- few-shot prompt
- structured outputs
- RAG if facts matter

### Step 4: Collect Data

Use realistic examples.

Clean:

- duplicates
- contradictions
- bad labels
- secrets
- formatting inconsistencies

### Step 5: Choose Method

Decision:

```text
Need behavior imitation? -> SFT
Need preference improvement? -> DPO/KTO/ORPO/SimPO
Need reasoning with verifiable reward? -> RL/RFT/RLVR
Need low cost open model tuning? -> LoRA/QLoRA
Need huge domain adaptation? -> continued pretraining + SFT
```

### Step 6: Train Small First

Run a small experiment:

- small sample
- short run
- low risk
- inspect outputs manually

Then scale.

### Step 7: Evaluate

Compare against baseline:

- aggregate metrics
- category slices
- edge cases
- human preference
- safety
- latency/cost

### Step 8: Iterate

Most gains come from:

- fixing labels
- adding hard examples
- balancing data
- removing noisy examples
- changing method only after data is healthy

### Step 9: Deploy Carefully

Use:

- staged rollout
- A/B test
- logging
- rollback plan
- monitoring
- periodic eval refresh

## 21. Fine-Tuning For Common Use Cases

### 21.1 Classification

Best method:

- SFT
- maybe smaller fine-tuned model

Data:

```json
{"input": "I was charged twice", "output": "billing_issue"}
```

Tips:

- balance labels
- include ambiguous cases
- define tie-breaking rules
- return only labels
- evaluate confusion matrix

### 21.2 Extraction

Best method:

- SFT + structured outputs

Tips:

- train valid JSON
- include missing-field examples
- preserve exact strings when needed
- validate schema
- evaluate field-level accuracy

### 21.3 Style And Tone

Best method:

- SFT for imitation
- DPO for preference refinement

Tips:

- include many realistic contexts
- avoid repetitive outputs
- include "bad tone" rejected examples
- pairwise eval works well

### 21.4 Domain Assistant

Best method:

- RAG for facts
- SFT for behavior/style
- DPO for answer quality

Important:

```text
Do not fine-tune a private wiki into the model if the wiki changes often.
Use RAG for knowledge and fine-tuning for behavior.
```

### 21.5 Code

Best method:

- SFT on code tasks
- RL with tests for code correctness
- repository-aware RAG for project-specific context

Tips:

- evaluate by running tests
- include compile errors
- include style conventions
- avoid training on secrets

### 21.6 Reasoning

Best method:

- SFT for basic solution style
- RLVR/RFT for verifiable correctness

Tips:

- final answer verification matters
- reward design is everything
- evaluate on held-out hard problems
- avoid rewarding verbosity

## 22. Fine-Tuning And RAG Together

They solve different problems.

RAG:

- supplies facts at inference
- supports citations
- updates without retraining
- handles private/current knowledge

Fine-tuning:

- teaches behavior
- teaches output format
- teaches domain style
- reduces prompt length
- improves repeated task performance

Best combined pattern:

```text
RAG retrieves evidence.
Fine-tuned model knows how to use evidence correctly.
Validator checks citations and format.
```

Example:

```text
RAG provides policy sections.
Fine-tuned model answers in company-approved support style.
Citation validator checks every claim.
```

## 23. Fine-Tuning Math Without Pain

### 23.1 Cross-Entropy

For SFT, the model predicts each next assistant token.

If the correct token is assigned high probability, loss is low.

If the correct token is assigned low probability, loss is high.

```text
loss = -log P(correct token)
```

Training adjusts weights to make target outputs more likely.

### 23.2 DPO Intuition

DPO trains preference:

```text
P(chosen answer) should increase
P(rejected answer) should decrease
but do not drift too far from reference model
```

The reference model matters because without it, the model can over-optimize and lose general behavior.

### 23.3 LoRA Intuition

LoRA assumes the needed task adaptation can be represented by a low-rank update.

Instead of changing a giant matrix:

```text
W_new = W + ΔW
```

LoRA represents:

```text
ΔW = B A
```

where `A` and `B` are much smaller.

That is why it saves memory.

## 24. Checklists

### 24.1 Before Fine-Tuning

- Do we have evals?
- Did prompting fail?
- Did RAG solve the knowledge issue?
- Is the behavior stable enough to train?
- Do we have representative data?
- Is the data legally usable?
- Are secrets/PII removed?
- Do we have a holdout test set?
- Do we know what success means?

### 24.2 Data Checklist

- realistic inputs
- consistent outputs
- no duplicates
- no test leakage
- no secrets
- enough edge cases
- balanced categories
- clear refusal examples
- format validity
- reviewed hard examples

### 24.3 Training Checklist

- correct tokenizer/chat template
- correct loss masking
- max sequence length checked
- validation split
- hyperparameters logged
- checkpoints saved
- seed logged
- training curves monitored
- small run before full run

### 24.4 Deployment Checklist

- eval pass
- safety pass
- latency/cost pass
- rollback plan
- model/version name recorded
- training data version recorded
- prompt version recorded
- monitoring enabled
- retraining trigger defined

## 25. Interview-Ready Answers

### "What is fine-tuning?"

```text
Fine-tuning is additional training of a pretrained model on task-specific examples so the desired behavior becomes part of the model, rather than something we only ask for in the prompt. It is best for stable behavior, format, style, classification, extraction, and domain adaptation. It is not the best way to store changing facts; for that I would use RAG.
```

### "When would you fine-tune instead of using RAG?"

```text
I use RAG when the model needs external or changing knowledge. I fine-tune when I need consistent behavior: a specific output schema, tone, classification policy, extraction style, or expert decision pattern. In many systems I combine them: RAG supplies evidence, and the fine-tuned model learns how to use that evidence.
```

### "What is LoRA?"

```text
LoRA is parameter-efficient fine-tuning. It freezes the original model weights and trains small low-rank matrices that act as task-specific updates. This gives much of the benefit of fine-tuning with far less memory and storage than updating every model parameter.
```

### "What is QLoRA?"

```text
QLoRA keeps the base model quantized, often in 4-bit precision, and trains LoRA adapters on top. It makes fine-tuning large open-weight models possible on much smaller hardware while preserving much of full fine-tuning quality.
```

### "What is DPO?"

```text
DPO is a preference optimization method. Instead of training a separate reward model and using PPO like classic RLHF, it directly trains the model on chosen and rejected responses, increasing the likelihood of preferred answers and decreasing the likelihood of rejected ones while staying close to a reference model.
```

### "How do you run a fine-tuning project?"

```text
I start with evals and a strong prompt baseline. Then I collect realistic training examples, clean and split the data, choose SFT/LoRA/DPO/RL depending on the objective, run a small experiment, compare against baseline on a held-out test set, inspect failures by category, iterate on data, and only then deploy with monitoring and rollback.
```

### "What are the biggest risks?"

```text
The biggest risks are bad data, overfitting, catastrophic forgetting, memorization of sensitive data, safety regressions, and optimizing the wrong thing. Fine-tuning amplifies whatever is in the dataset, so data quality and evaluation are more important than the training command.
```

## 26. Quick Glossary

| Term | Meaning |
| --- | --- |
| Base model | pretrained model before instruction tuning |
| Instruct model | model fine-tuned to follow instructions |
| Chat model | instruction model trained for multi-turn role-based conversation |
| SFT | supervised fine-tuning on ideal responses |
| DAPT | domain-adaptive continued pretraining |
| PEFT | parameter-efficient fine-tuning |
| LoRA | low-rank adapter fine-tuning |
| QLoRA | LoRA on quantized base model |
| Adapter | small trainable module added to frozen model |
| DPO | direct preference optimization |
| RLHF | reinforcement learning from human feedback |
| PPO | policy optimization method used in classic RLHF |
| RFT | reinforcement fine-tuning |
| RLVR | reinforcement learning with verifiable rewards |
| GRPO | group-relative policy optimization |
| Reward model | model that scores outputs |
| Reference model | baseline model used to constrain preference optimization |
| Catastrophic forgetting | losing old abilities after fine-tuning |
| Overfitting | memorizing training data instead of generalizing |
| Checkpoint | saved model state during/after training |
| Adapter merge | combining LoRA adapter weights into base weights |
| Distillation | training a smaller model to imitate a larger/stronger model |

## 27. References

- OpenAI model optimization and fine-tuning docs: [Model optimization](https://platform.openai.com/docs/guides/fine-tuning)
- OpenAI supervised fine-tuning docs: [Supervised fine-tuning](https://platform.openai.com/docs/guides/supervised-fine-tuning)
- OpenAI DPO docs: [Direct preference optimization](https://platform.openai.com/docs/guides/direct-preference-optimization)
- OpenAI reinforcement fine-tuning docs: [Reinforcement fine-tuning](https://platform.openai.com/docs/guides/reinforcement-fine-tuning)
- Hugging Face PEFT docs: [PEFT](https://huggingface.co/docs/peft/index)
- Hugging Face LoRA docs: [LoRA](https://huggingface.co/docs/peft/developer_guides/lora)
- Hugging Face TRL docs: [TRL](https://huggingface.co/docs/trl)
- LoRA paper: [Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- QLoRA paper: [Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)
- InstructGPT / RLHF paper: [Training Language Models to Follow Instructions with Human Feedback](https://arxiv.org/abs/2203.02155)
- FLAN paper: [Scaling Instruction-Finetuned Language Models](https://arxiv.org/abs/2210.11416)
- Flan Collection: [Designing Data and Methods for Effective Instruction Tuning](https://arxiv.org/abs/2301.13688)
- Self-Instruct: [Aligning Language Models with Self-Generated Instructions](https://arxiv.org/abs/2212.10560)
- DPO paper: [Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- KTO paper: [Model Alignment as Prospect Theoretic Optimization](https://arxiv.org/abs/2402.01306)
- ORPO paper: [Monolithic Preference Optimization without Reference Model](https://arxiv.org/abs/2403.07691)
- SimPO paper: [Simple Preference Optimization with a Reference-Free Reward](https://arxiv.org/abs/2405.14734)
- DeepSeek-R1 / GRPO reasoning training: [Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948)

