# Modern LLM Engineering: How LLMs Are Built Inside

Prepared for interview preparation and real system design. Updated May 2026.

This guide explains how modern large language models are engineered end to end: transformer internals, data, pretraining, post-training, reinforcement learning, reasoning models, fine-tuning, distillation, quantization, inference systems, and the practical tricks teams use to make models work.

The short version:

```text
Modern LLMs are built in three big phases:

1. Pretraining:
   learn general language/code/world patterns by predicting tokens at huge scale.

2. Post-training:
   turn the raw model into a useful assistant through SFT, preference tuning, safety tuning, and RL.

3. Serving optimization:
   make the model fast, cheap, reliable, and controllable in production.
```

## 1. The Big Picture

A modern LLM is not just a neural network. It is a full engineering stack:

```text
data pipeline
  -> tokenizer
  -> transformer architecture
  -> distributed pretraining
  -> instruction tuning
  -> preference alignment
  -> reinforcement learning
  -> safety tuning
  -> evaluation
  -> compression / quantization
  -> inference runtime
  -> monitoring and iteration
```

Each layer matters. A model can fail because of bad data, weak tokenizer, poor architecture choice, unstable training, bad post-training data, reward hacking, quantization damage, decoding settings, or serving bottlenecks.

Good interview line:

> The model weights are only the visible artifact. The real system is the data, training recipe, post-training recipe, eval suite, and inference stack around those weights.

## 2. Core Terminology

| Term | Meaning |
| --- | --- |
| Token | Unit of text the model reads and predicts |
| Tokenizer | Algorithm that converts text into token IDs |
| Vocabulary | Set of possible tokens |
| Embedding | Vector representation of a token |
| Transformer | Neural architecture built from attention, MLPs, residual streams, and normalization |
| Decoder-only model | Autoregressive model that predicts the next token from previous tokens |
| Logits | Raw scores over the vocabulary before softmax |
| Softmax | Converts logits into probabilities |
| Context window | Maximum number of tokens the model can attend to |
| Pretraining | Large-scale next-token prediction training |
| Post-training | Training after pretraining to make the model useful and aligned |
| SFT | Supervised fine-tuning on ideal demonstrations |
| RLHF | Reinforcement learning from human feedback |
| RLAIF | Reinforcement learning from AI feedback |
| DPO | Direct preference optimization on chosen/rejected responses |
| RLVR | Reinforcement learning with verifiable rewards |
| GRPO | Group-relative policy optimization, used in some reasoning-model training |
| MoE | Mixture of Experts, sparse architecture where only some experts activate per token |
| Dense model | Model where all parameters are used for every token |
| Active parameters | Parameters used for a given token in sparse/MoE inference |
| Distillation | Training a smaller model to imitate a larger/stronger model |
| Quantization | Lowering numerical precision to reduce memory and compute |
| KV cache | Cached attention keys/values used for faster autoregressive decoding |
| Speculative decoding | Faster decoding using a small draft model plus large verifier model |

## 3. What A Language Model Actually Learns

The base objective is simple:

```text
Given previous tokens, predict the next token.
```

Example:

```text
Input tokens:
"The capital of France is"

Target next token:
" Paris"
```

Training repeats this trillions of times. From this objective, models learn:

- grammar
- facts
- style
- code patterns
- translation
- reasoning patterns
- world regularities
- instruction-like behavior if such data is present

The surprising part is that many capabilities emerge from next-token prediction when scale, data diversity, and architecture are strong enough.

But a pretrained base model is not automatically a good assistant. It predicts plausible continuations. Post-training teaches it to follow instructions, be helpful, use tools, refuse unsafe requests, and produce preferred formats.

## 4. Tokenization

Tokenization is the first design choice.

### 4.1 Why Tokens Exist

Neural nets process fixed IDs, not raw text. Tokenization maps strings to integers.

```text
"mechanistic interpretability"
-> [token_id_1, token_id_2, token_id_3]
```

Common tokenizer families:

- BPE: byte pair encoding
- WordPiece
- SentencePiece / unigram
- byte-level BPE

Modern LLMs often use byte-aware tokenizers so they can represent arbitrary text.

### 4.2 Why Tokenization Matters

Tokenizer quality affects:

- multilingual performance
- code performance
- math tokenization
- rare names
- compression ratio
- context efficiency
- spelling robustness
- latency and cost

Example:

```text
If a non-English sentence takes twice as many tokens as English,
the model effectively has less context and higher cost for that language.
```

### 4.3 Vocabulary Size Tradeoff

Larger vocabulary:

- fewer tokens per text
- bigger embedding/unembedding matrices
- potentially better multilingual/code compression

Smaller vocabulary:

- simpler
- smaller embedding matrices
- more tokens for the same text

Modern vocabularies are often large because token efficiency matters for long-context and multilingual systems.

### 4.4 Chat Templates

Chat models are still token predictors. A chat template converts messages into text/tokens.

Conceptually:

```text
<system>
You are helpful.
<user>
Explain RLHF.
<assistant>
```

Wrong chat templates can damage performance. During fine-tuning and inference, the template must match how the model was trained.

## 5. Transformer Architecture

Most modern LLMs are decoder-only transformers.

### 5.1 Decoder-Only Transformer Flow

```text
tokens
  -> token embeddings
  -> positional information
  -> repeated transformer blocks
       -> attention
       -> MLP
       -> residual connections
       -> normalization
  -> final norm
  -> unembedding
  -> logits over next token
```

Decoder-only means the model predicts left-to-right with a causal mask:

```text
token at position t can attend to positions <= t
```

### 5.2 Residual Stream

The residual stream is the model's information highway.

Each layer reads it and writes updates back:

```text
x = x + attention_update
x = x + mlp_update
```

This makes very deep networks trainable and lets information accumulate across layers.

### 5.3 Attention

Attention lets each token position read from previous positions.

For each token, the model computes:

```text
query Q
key K
value V
```

Attention scores:

```text
score = QK^T / sqrt(d)
```

Then softmax turns scores into attention weights, and the model reads a weighted sum of values.

Intuition:

```text
Q asks: what am I looking for?
K says: what do I contain?
V says: what information should be copied if attended to?
```

### 5.4 Multi-Head Attention

One attention head cannot track everything. Multi-head attention runs many attention operations in parallel.

Different heads may specialize in:

- previous token
- matching brackets
- copying names
- tracking entities
- attending to instructions
- retrieving relevant context
- detecting delimiters

### 5.5 MLP Blocks

MLPs are per-token nonlinear processors.

They often act like feature detectors and feature writers:

```text
if feature X is present:
  write feature Y into residual stream
```

Modern LLM MLPs often use gated activations such as SwiGLU.

### 5.6 Normalization

Normalization keeps activations stable.

Modern models often use RMSNorm rather than LayerNorm.

Common pattern:

```text
pre-norm transformer:
  x = x + attention(norm(x))
  x = x + mlp(norm(x))
```

Pre-norm improves training stability for deep transformers.

### 5.7 Positional Encoding

Transformers need position information.

Common approaches:

- learned absolute position embeddings
- sinusoidal embeddings
- RoPE: rotary positional embeddings
- ALiBi-style biases

RoPE is widely used in modern LLMs because it works well with relative position behavior and long-context extension methods.

### 5.8 Output Layer

The final hidden state is projected to vocabulary logits.

```text
hidden vector -> unembedding matrix -> logits
```

Then decoding chooses the next token using greedy, sampling, beam-like, or constrained methods.

## 6. Modern Architecture Tricks

### 6.1 Grouped-Query Attention And Multi-Query Attention

Standard attention has separate K/V heads for each query head.

Multi-query attention shares one set of K/V heads across many query heads.

Grouped-query attention is in between:

```text
many query heads
fewer key/value heads
```

Why:

- reduces KV cache memory
- improves inference speed
- preserves more quality than full multi-query in many settings

GQA is common in modern production LLMs.

### 6.2 FlashAttention

Attention is memory-hungry. Naive attention materializes a large attention matrix.

FlashAttention computes exact attention using IO-aware tiling to reduce memory movement.

Why it matters:

- faster training
- lower memory
- enables longer context
- improves GPU utilization

This is a systems trick, not a model behavior trick.

### 6.3 Sliding Window And Local Attention

For long context, not every token always needs to attend to every previous token.

Sliding-window attention restricts attention to recent tokens.

Pros:

- cheaper long context
- lower memory

Cons:

- can miss long-range dependencies

Some models combine local attention with occasional global attention or other long-context mechanisms.

### 6.4 Mixture Of Experts

MoE models have many expert MLPs, but only activate a few per token.

```text
token representation
  -> router
  -> choose top-k experts
  -> run selected experts
  -> combine outputs
```

Why MoE:

- many total parameters
- lower active compute per token
- better capacity/cost tradeoff

Example:

```text
Total parameters: 200B
Active parameters per token: 30B
```

Challenges:

- router instability
- load balancing
- expert specialization
- distributed communication
- harder serving
- expert collapse if router overuses some experts

### 6.5 Multi-Token Prediction

Some modern training recipes predict more than one future token.

Why:

- richer training signal
- potentially faster inference with special decoding
- encourages planning over longer spans

Tradeoff:

- more architecture/training complexity

### 6.6 Latent Attention And KV Compression

Some recent models reduce KV cache cost by compressing keys/values into lower-dimensional latent states or using architectural variants that make long-context inference cheaper.

Goal:

```text
long context without exploding memory
```

This matters because KV cache memory becomes a dominant cost during serving.

## 7. Data Engineering

Data is the model's real curriculum.

### 7.1 Pretraining Data Sources

Common sources:

- web crawl
- books
- code
- academic papers
- forums
- Q&A sites
- encyclopedic text
- math data
- multilingual corpora
- synthetic data
- licensed data
- human-written instruction data

High-performing models usually use carefully filtered and mixed data, not raw internet dumps.

### 7.2 Data Filtering

Filtering removes:

- spam
- boilerplate
- adult/unsafe content depending on policy
- duplicated pages
- low-quality machine translations
- corrupted text
- personally identifiable information
- malware/code abuse data depending on policy
- benchmark contamination

Quality filters can be:

- rule-based
- classifier-based
- language ID
- perplexity-based
- embedding-based
- model-scored
- source reputation based

### 7.3 Deduplication

Dedup removes repeated data.

Why:

- reduces memorization
- prevents overrepresenting popular pages
- improves training efficiency
- reduces benchmark leakage

Types:

- exact dedup
- near-dedup with MinHash or similarity hashing
- document-level dedup
- paragraph/span-level dedup

### 7.4 Data Mixture

Training data is mixed by category.

Example mixture:

```text
web text:        45%
code:            20%
math:            10%
books/papers:    10%
multilingual:    10%
synthetic:        5%
```

The exact mixture strongly affects model personality and capabilities.

More code data can improve:

- programming
- structured reasoning
- tool use
- exact syntax

More math data can improve:

- symbolic manipulation
- stepwise reasoning
- precision

More high-quality instruction-like data can make base models easier to post-train.

### 7.5 Data Curriculum

Not all data must be used uniformly throughout training.

Curriculum strategies:

- start broad, end high-quality
- upweight hard data later
- anneal toward instruction/code/math data
- use long-context data later
- mix synthetic reasoning data during late pretraining

The final training phase can disproportionately shape model behavior.

### 7.6 Benchmark Decontamination

If benchmark examples appear in training data, eval scores become misleading.

Decontamination:

- search training corpus for benchmark overlap
- remove exact/near matches
- inspect paraphrase leakage where possible

This is hard and imperfect, but necessary for credible claims.

## 8. Scaling Laws

Scaling laws describe how model loss changes with:

- parameter count
- dataset size
- compute

The older intuition:

```text
bigger model + more data + more compute = lower loss
```

The Chinchilla insight:

```text
Many early large models were undertrained.
For a fixed compute budget, train smaller models on more tokens than previously assumed.
```

Modern practice:

- train models on many more tokens than parameter count alone suggests
- optimize for inference economics, not just training loss
- overtrain smaller dense models because they are cheaper to serve
- use MoE to increase capacity without proportional active compute

## 9. Pretraining

### 9.1 Objective

Most decoder LLMs use causal language modeling:

```text
loss = average cross-entropy over next-token predictions
```

The model sees:

```text
tokens[0:n-1]
```

and predicts:

```text
tokens[1:n]
```

This is teacher forcing: during training, the model sees true previous tokens, not its own sampled outputs.

### 9.2 Training Loop

Simplified:

```text
sample batch of token sequences
forward pass
compute next-token loss
backpropagate
update weights
repeat millions of times
```

### 9.3 Optimizer

Common:

- AdamW
- beta settings tuned for large-scale training
- weight decay
- gradient clipping
- learning-rate warmup
- cosine or linear decay

### 9.4 Precision

Training uses lower precision for efficiency:

- FP32 for some master states historically
- FP16
- BF16
- FP8 in newer large-scale training stacks

BF16 is popular because it has a larger exponent range than FP16 and is more stable.

### 9.5 Training Stability

Large training runs can fail because of:

- loss spikes
- bad data shards
- numerical overflow
- optimizer instability
- hardware failures
- distributed communication failures
- MoE routing collapse
- gradient explosions

Stability tricks:

- warmup schedules
- gradient clipping
- careful initialization
- normalization choice
- BF16/FP8 recipes
- loss spike detection
- checkpoint rollback
- data quality monitoring
- skip bad batches
- use smaller pilot runs before full scale

## 10. Distributed Training

Large models do not fit on one GPU.

Modern training combines several parallelism strategies.

### 10.1 Data Parallelism

Each GPU has a model copy and processes different data.

Gradients are synchronized.

Pros:

- simple
- scales well up to a point

Cons:

- each GPU must fit the full model

### 10.2 Tensor Parallelism

Split large matrices across GPUs.

Example:

```text
one giant MLP matrix -> shards across multiple GPUs
```

Pros:

- allows larger layers

Cons:

- frequent communication

### 10.3 Pipeline Parallelism

Split model layers across GPUs.

```text
GPU 1: layers 1-10
GPU 2: layers 11-20
GPU 3: layers 21-30
```

Microbatches flow through the pipeline.

Issue:

- pipeline bubbles: idle time if scheduling is poor

### 10.4 Sequence / Context Parallelism

Split the sequence dimension across GPUs.

Useful for:

- long-context training
- attention memory reduction

### 10.5 ZeRO / FSDP

Optimizer states, gradients, and parameters consume huge memory.

ZeRO and Fully Sharded Data Parallel split these across GPUs.

Stages conceptually:

```text
shard optimizer states
shard gradients
shard parameters
```

This enables training much larger models.

### 10.6 Activation Checkpointing

Activations consume memory during backprop.

Checkpointing stores fewer activations and recomputes them during backward pass.

Tradeoff:

```text
less memory, more compute
```

### 10.7 Training Infrastructure

Large training needs:

- high-bandwidth GPU interconnect
- fast storage
- fault-tolerant checkpointing
- deterministic data sharding
- experiment tracking
- cluster scheduler
- monitoring dashboards
- automatic restart
- data loader performance tuning

At frontier scale, training is a distributed systems problem as much as an ML problem.

## 11. From Base Model To Assistant

A pretrained base model predicts continuations.

An assistant model follows instructions.

Post-training is the bridge:

```text
base model
  -> supervised fine-tuning
  -> preference tuning
  -> safety tuning
  -> tool/use-case tuning
  -> RL or reasoning tuning
  -> final model
```

## 12. Supervised Fine-Tuning

SFT trains the model on ideal instruction-response examples.

Example:

```json
{
  "messages": [
    {"role": "user", "content": "Summarize this paragraph in one sentence."},
    {"role": "assistant", "content": "The paragraph argues that careful data filtering improves model quality."}
  ]
}
```

SFT teaches:

- follow instructions
- answer in chat format
- use desired tone
- produce structured outputs
- imitate expert demonstrations
- call tools in the right format

SFT does not fully solve:

- preference tradeoffs
- safety edge cases
- deep reasoning
- hallucination

Data quality matters more than volume.

## 13. Preference Optimization

SFT says:

```text
imitate this answer
```

Preference optimization says:

```text
prefer this answer over that answer
```

### 13.1 Preference Data

Format:

```json
{
  "prompt": "Explain gradient descent to a beginner.",
  "chosen": "Gradient descent is a method for improving a model by taking small steps in the direction that reduces error.",
  "rejected": "Gradient descent is when gradients descend through layers and make the AI smarter."
}
```

Humans or AI graders can provide preferences.

### 13.2 RLHF

Classic RLHF:

```text
1. Train SFT model.
2. Collect human preferences.
3. Train reward model.
4. Use PPO or similar RL method to optimize policy against reward model.
5. Add KL penalty so model does not drift too far.
```

Why RLHF worked:

- humans can compare answers more easily than write perfect ones
- reward model scales preference feedback
- RL optimizes behavior toward reward

Problems:

- reward model can be wrong
- reward hacking
- training instability
- expensive preference data
- model may become overly cautious or sycophantic

### 13.3 DPO

DPO skips the explicit reward model.

It directly trains on chosen/rejected pairs.

Intuition:

```text
increase chosen response likelihood
decrease rejected response likelihood
stay close to reference model
```

Why popular:

- simpler than PPO-based RLHF
- stable
- easy to run on open models
- strong for style/helpfulness alignment

### 13.4 Other Preference Methods

Modern post-training may use:

- IPO
- KTO
- ORPO
- SimPO
- rejection sampling
- best-of-N sampling
- AI feedback
- constitutional feedback

They differ in whether they need paired preferences, a reference model, or explicit rewards.

## 14. Reinforcement Learning For LLMs

Reinforcement learning trains the model to maximize a reward.

For LLMs:

```text
state = prompt + generated tokens so far
action = next token
policy = language model
reward = score for final answer or process
```

### 14.1 Why RL Is Hard For LLMs

The action space is huge:

```text
vocabulary size: often 100k+ tokens
```

Rewards are sparse:

```text
one final answer may get one score
```

Training can be unstable:

- reward hacking
- mode collapse
- verbosity gaming
- KL drift
- degraded language quality

### 14.2 PPO In RLHF

PPO updates the policy while limiting how far it moves per step.

In RLHF, PPO often uses:

- policy model
- reference model
- reward model
- value model / critic
- KL penalty

Objective:

```text
maximize reward - beta * KL(policy || reference)
```

KL penalty prevents the model from exploiting reward model flaws too aggressively.

### 14.3 RL With Verifiable Rewards

RLVR uses rewards that can be checked automatically.

Examples:

- math answer correct
- code passes tests
- SQL query returns expected result
- theorem checker passes
- exact extraction matches gold label
- unit tests pass

Why it matters:

- less dependent on subjective reward models
- strong for reasoning and code
- can generate many attempts and score them cheaply

### 14.4 GRPO And Group-Relative Updates

GRPO-style training samples multiple outputs for the same prompt and scores them.

Conceptually:

```text
prompt -> sample N completions
score each completion
compute group-relative advantage
increase probability of above-average completions
decrease probability of below-average completions
```

Why useful:

- avoids a separate critic in some implementations
- works well when final answers can be graded
- became prominent in reasoning-model training discussions after DeepSeekMath/DeepSeek-R1

### 14.5 Outcome Rewards vs Process Rewards

Outcome reward:

```text
final answer is correct or incorrect
```

Process reward:

```text
intermediate reasoning steps are good or bad
```

Outcome rewards are easier to automate for math/code. Process rewards can guide reasoning more directly but require step-level labels or reliable judges.

### 14.6 Reward Hacking

Reward hacking happens when the model finds a way to get high reward without actually doing the intended task.

Examples:

- verbose answer gets high helpfulness score
- model formats answer to fool grader
- code hardcodes tests
- model learns dataset artifacts
- model over-refuses because safe refusals avoid penalties

Mitigations:

- adversarial evals
- multiple graders
- hidden tests
- reward model audits
- KL constraints
- human review
- diverse training prompts
- separate final-answer and behavior metrics

## 15. Reasoning Models

Reasoning models are trained to spend more computation on hard problems.

They often use:

- math/code/verifiable tasks
- longer generated reasoning traces
- RL with verifiable rewards
- rejection sampling
- distillation from stronger reasoning models
- test-time compute scaling

### 15.1 Test-Time Compute

Instead of giving one quick answer, the system can:

- sample multiple solutions
- search over solution paths
- verify candidates
- choose best answer
- spend more tokens thinking

Tradeoff:

```text
better accuracy, higher latency and cost
```

### 15.2 Rejection Sampling

Generate many answers, keep the ones that pass a verifier.

Example:

```text
sample 64 code solutions
run unit tests
keep passing solution
```

This can also create training data:

```text
successful sampled solutions -> SFT dataset
```

### 15.3 Chain-Of-Thought Distillation

A strong model generates reasoning traces. A smaller model trains on them.

Why:

- transfer reasoning style
- make smaller models stronger
- reduce inference cost

Risk:

- distills teacher errors
- may train superficial reasoning imitation
- traces may be verbose or unfaithful

### 15.4 The Key Modern Pattern

For hard reasoning:

```text
SFT teaches format and basic reasoning style.
RLVR teaches solution search that earns verifiable reward.
Distillation compresses expensive reasoning into cheaper models.
```

## 16. Safety And Alignment Engineering

Safety is trained and engineered at multiple layers.

### 16.1 Data-Level Safety

During pretraining:

- filter harmful content
- balance refusals and benign knowledge
- remove secrets/PII
- reduce toxic or abusive data

Tradeoff:

- over-filtering can damage useful capabilities
- under-filtering can increase harmful behavior

### 16.2 SFT Safety

Teach:

- safe completions
- refusals
- redirections
- policy-compliant alternatives
- privacy-preserving behavior

### 16.3 Preference Safety

Use chosen/rejected pairs:

```text
chosen: safe, helpful refusal or safe alternative
rejected: harmful compliance
```

### 16.4 Constitutional / AI Feedback

AI feedback can critique responses using written principles.

Example principles:

- do not reveal private data
- avoid harmful instructions
- be honest about uncertainty
- prefer safe alternatives

This scales feedback but depends on the judge model and principles.

### 16.5 Runtime Safety

Production systems add:

- classifiers
- policy engines
- tool permission checks
- output filters
- abuse monitoring
- rate limits
- human escalation
- logging and audits

Training alone is not enough.

## 17. Fine-Tuning And Adaptation

Not every team trains frontier models from scratch. Most adapt existing models.

Methods:

- prompt engineering
- RAG
- supervised fine-tuning
- LoRA
- QLoRA
- DPO
- reinforcement fine-tuning
- distillation

Rule:

```text
Use RAG for facts.
Use fine-tuning for stable behavior.
Use RL/RFT when rewards are reliable and examples are insufficient.
```

### 17.1 LoRA

LoRA freezes base weights and trains low-rank adapters.

```text
W_new = W + BA
```

Why:

- cheap
- memory efficient
- store many adapters
- good for task adaptation

### 17.2 QLoRA

QLoRA trains LoRA adapters on top of a quantized base model.

Why:

- fine-tune larger models on smaller hardware
- strong quality/cost tradeoff

### 17.3 Distillation

Distillation trains a smaller model from a larger teacher.

Sources:

- teacher answers
- teacher reasoning traces
- teacher preference labels
- teacher tool calls
- teacher critiques

Why:

- cheaper serving
- lower latency
- specialized small models

Risk:

- copies teacher mistakes
- narrows behavior
- may lose robustness

## 18. Decoding

After the model produces logits, decoding chooses tokens.

### 18.1 Greedy Decoding

Always choose highest-probability token.

Pros:

- deterministic
- fast

Cons:

- can be dull
- can get stuck

### 18.2 Temperature

Temperature changes randomness.

```text
lower temperature -> sharper distribution -> more deterministic
higher temperature -> flatter distribution -> more diverse
```

Use low temperature for:

- extraction
- classification
- code fixes
- grounded answers

Use higher temperature for:

- brainstorming
- creative writing
- diverse sampling

### 18.3 Top-p And Top-k

Top-k:

```text
sample only from k most likely tokens
```

Top-p:

```text
sample from smallest set of tokens whose total probability >= p
```

Top-p is also called nucleus sampling.

### 18.4 Beam Search

Beam search keeps multiple candidate sequences.

It is common in translation but less central for chat LLMs because it can produce generic or overly optimized text.

### 18.5 Constrained Decoding

Constrained decoding masks invalid tokens.

Use for:

- JSON schema
- regex
- grammar
- tool-call arguments
- enums

Important:

```text
Constrained decoding guarantees format, not truth.
```

## 19. Inference Engineering

Serving LLMs is hard because autoregressive decoding is sequential.

### 19.1 Prefill And Decode

Inference has two phases:

```text
prefill:
  process the whole prompt in parallel

decode:
  generate one token at a time
```

Prefill is compute-heavy.

Decode is memory-bandwidth-heavy because each new token reads the KV cache.

### 19.2 KV Cache

During generation, the model caches keys and values for previous tokens.

Without KV cache:

```text
recompute all previous attention states every token
```

With KV cache:

```text
reuse previous K/V states
```

KV cache enables fast generation but consumes lots of memory.

### 19.3 Continuous Batching

Requests arrive at different times and generate different lengths.

Continuous batching dynamically batches active requests together.

Why:

- improves GPU utilization
- reduces cost
- handles variable-length generation

### 19.4 PagedAttention

PagedAttention manages KV cache like virtual memory pages.

Why:

- reduces memory fragmentation
- enables efficient batching
- supports many concurrent requests

This is a key idea behind vLLM-style serving.

### 19.5 Speculative Decoding

Speculative decoding uses:

- small fast draft model
- large target model

Flow:

```text
draft model proposes several tokens
large model verifies them in parallel
accepted tokens are emitted
rejected token corrected by large model
```

Why:

- preserves target model distribution
- speeds decoding when draft model is accurate

### 19.6 Prompt Caching

If many requests share the same prefix, cache its computed states.

Useful for:

- long system prompts
- RAG with repeated source context
- agent instructions
- coding environments
- enterprise policies

### 19.7 Quantized Inference

Quantization reduces precision:

- FP16/BF16
- FP8
- INT8
- INT4

Benefits:

- lower memory
- faster inference
- cheaper serving

Risks:

- quality loss
- brittle tool calls
- worse math/code
- long-context degradation

Always re-evaluate after quantization.

## 20. Memory And Compute Economics

LLM cost depends on:

- parameters
- active parameters
- sequence length
- batch size
- precision
- KV cache size
- decoding length
- hardware utilization

### 20.1 Training Cost

Training compute roughly scales with:

```text
parameters * training tokens
```

More exact estimates include forward/backward pass constants, optimizer overhead, and hardware efficiency.

### 20.2 Inference Cost

Inference cost differs by phase:

```text
prefill cost ~ prompt length
decode cost ~ output length and model size
KV memory ~ batch size * context length * layers * hidden dimensions
```

Long prompts are expensive in prefill.

Long generations are expensive in decode.

Long contexts are expensive in KV memory.

### 20.3 Dense vs MoE Economics

Dense:

```text
all parameters active per token
```

MoE:

```text
many total parameters
few active experts per token
```

MoE can be cheaper per token for a given total capacity, but harder to train and serve.

## 21. Long Context Engineering

Long context is not just increasing a number.

Challenges:

- attention cost
- KV cache memory
- position encoding extrapolation
- retrieval inside context
- lost-in-the-middle behavior
- data scarcity for long-context training
- evaluation difficulty

Techniques:

- RoPE scaling
- long-context continued training
- sliding-window attention
- sparse/global attention
- retrieval-augmented context
- memory compression
- KV cache compression
- prompt caching

Important:

```text
Long context does not eliminate RAG.
It changes the boundary where retrieval becomes necessary.
```

## 22. Multimodal LLM Engineering

Modern models may handle:

- text
- images
- audio
- video
- screen/UI state
- documents

Typical architecture:

```text
modality encoder
  -> projection into LLM token space
  -> language model processes mixed tokens
  -> text/tool/action output
```

Vision-language models often use:

- vision transformer encoder
- image patch tokens
- connector/projector
- text decoder

Challenges:

- grounding visual details
- OCR
- spatial reasoning
- hallucinated visual claims
- video length
- multimodal safety

## 23. Tool Use And Function Calling

Models can be trained to call tools.

Tool training examples include:

```json
{
  "user": "What's the weather in Seattle tomorrow?",
  "assistant_tool_call": {
    "name": "get_weather",
    "arguments": {"location": "Seattle", "date": "tomorrow"}
  }
}
```

Engineering layers:

- tool schema
- tool-call constrained decoding
- argument validation
- permission checks
- tool result formatting
- final answer synthesis

Training helps the model decide when to call a tool. Runtime validation keeps tool use safe.

## 24. RAG vs Training

RAG and training solve different problems.

RAG:

- current facts
- private documents
- citations
- source-grounded answers

Training:

- behavior
- style
- reasoning habits
- tool-use format
- domain language

Best pattern:

```text
Use RAG to provide evidence.
Use post-training to teach the model how to use evidence.
Use validation to check citations and outputs.
```

## 25. Evals

Modern model engineering is eval-driven.

### 25.1 Pretraining Evals

Track:

- validation loss
- perplexity
- benchmark performance
- contamination checks
- data-slice performance
- multilingual/code/math metrics

### 25.2 Post-Training Evals

Track:

- instruction following
- helpfulness
- harmlessness
- honesty
- tool-call correctness
- format validity
- refusal accuracy
- hallucination rate
- preference win rate

### 25.3 Reasoning Evals

Track:

- math accuracy
- code pass rate
- proof/checker success
- hidden test performance
- robustness under paraphrase
- test-time compute curves

### 25.4 Serving Evals

Track:

- p50/p95 latency
- tokens/sec
- throughput
- cost/request
- GPU utilization
- batch efficiency
- cache hit rate
- error rate

## 26. "Hacks" That Actually Matter

These are practical engineering tricks, not shortcuts around safety.

### 26.1 Data Quality Beats Model Size

A smaller model trained on cleaner, better-mixed data can beat a larger model trained on noisy data.

Common data hacks:

- aggressive dedup
- quality classifiers
- source weighting
- late-stage high-quality annealing
- synthetic hard examples
- benchmark decontamination
- domain-specific upsampling

### 26.2 Rejection Sampling

Generate many candidate answers and keep the best according to a verifier.

Uses:

- data generation
- reasoning training
- code generation
- math solutions

### 26.3 Best-Of-N

At inference:

```text
sample N answers
score them
return best
```

Improves quality but increases cost and latency.

### 26.4 Self-Consistency

For reasoning:

```text
sample multiple reasoning paths
take majority final answer
```

Works best when final answers are easy to compare.

### 26.5 Distill Expensive Into Cheap

Use a strong model to create data, then train a smaller model.

Pattern:

```text
frontier model -> generate traces/labels/preferences
small model -> train on curated outputs
```

### 26.6 Use Verifiers

Do not trust generation when checking is possible.

Examples:

- run unit tests
- execute SQL
- validate JSON schema
- check citations
- verify math answer
- run static analysis

### 26.7 Prompt Cache Long Prefixes

If the same long instruction/context repeats, caching can massively reduce latency and cost.

### 26.8 Quantize Carefully

Quantization is a real serving win, but always test:

- reasoning
- code
- tool calls
- long context
- safety refusals
- rare languages

### 26.9 Separate Fast And Slow Paths

Not every query needs the biggest model.

Architecture:

```text
small classifier/router
  -> easy query: small model
  -> hard query: large model or reasoning mode
  -> factual query: RAG/tool path
```

### 26.10 Use Structured Outputs

For machine-facing tasks, make the model output structured data and validate it.

```text
schema-constrained generation + validation > hoping text parses
```

## 27. Common Failure Modes

| Failure | Where It Comes From | Fix |
| --- | --- | --- |
| memorization | duplicated/sensitive training data | dedup, redact, test extraction |
| hallucination | next-token objective + weak grounding | RAG, citations, verifier |
| sycophancy | preference data rewards agreement | better preference labels |
| over-refusal | safety data too broad | nuanced refusal data |
| under-refusal | weak safety training | adversarial safety data |
| reward hacking | flawed reward/grader | hidden tests, grader audits |
| mode collapse | aggressive post-training | KL, data diversity |
| bad tool calls | poor schemas/examples | tool SFT, constrained decoding |
| degraded quantized model | precision too low | better quantization, eval |
| long-context failure | attention/position/data limits | long-context training, RAG |
| MoE expert collapse | router imbalance | load balancing losses |
| training instability | LR/data/numerics | warmup, clipping, rollback |

## 28. How Modern Models Differ From Older Ones

Older pattern:

```text
dense decoder-only transformer
pretrain on broad web data
SFT + RLHF
serve with basic batching
```

Modern pattern:

```text
better tokenizer
cleaner and more curated data
more code/math/synthetic data
GQA / RoPE / FlashAttention
long-context training
MoE for capacity
SFT + preference optimization
RLVR/RFT for reasoning
distillation into smaller models
tool-use training
structured outputs
quantized/optimized serving
continuous batching and KV-cache management
eval-driven release gates
```

## 29. Practical System Design: Building An LLM Product

A production LLM product often looks like:

```text
request
  -> auth/rate limit
  -> safety/input classifier
  -> router
  -> RAG/tools if needed
  -> choose model size/reasoning mode
  -> generate with constraints
  -> verify output
  -> safety/output check
  -> log traces and eval signals
```

Model engineering and product engineering meet at:

- routing
- tool use
- RAG
- structured output
- safety
- latency/cost controls
- logging
- evals

## 30. Interview-Ready Answers

### "How are modern LLMs trained?"

```text
Modern LLMs are usually pretrained with next-token prediction on a huge curated corpus, then post-trained. Post-training typically includes supervised fine-tuning on instruction-response examples, preference optimization such as RLHF or DPO, safety tuning, tool-use tuning, and increasingly reinforcement learning with verifiable rewards for reasoning-heavy tasks. Finally, models are evaluated, compressed, and optimized for serving.
```

### "What happens inside a transformer?"

```text
Tokens are embedded into vectors, positional information is added, and the vectors pass through repeated transformer blocks. Attention moves information between token positions, MLPs transform features within each position, residual connections carry information forward, and the final hidden state is projected into logits over the vocabulary for next-token prediction.
```

### "Why do we need RL after SFT?"

```text
SFT teaches the model to imitate demonstrations. RL or preference optimization teaches it to prefer better outputs according to human or verifiable rewards. This matters when there are many possible answers, when quality is easier to judge than demonstrate, or when reasoning tasks benefit from exploration and reward feedback.
```

### "What is RLHF?"

```text
RLHF collects human preferences over model outputs, trains a reward model to predict those preferences, and then optimizes the language model against that reward, usually with a KL penalty to keep it close to the original model. It helps align the model with human judgments but can suffer from reward hacking and reward model errors.
```

### "What changed with reasoning models?"

```text
Reasoning models use more test-time compute and are often trained with verifiable rewards. Instead of only imitating answers, they sample solution attempts, receive rewards from math checkers, code tests, or graders, and learn solution-search behavior. Distillation can then transfer expensive reasoning behavior into cheaper models.
```

### "What are the biggest engineering bottlenecks?"

```text
At training time, the bottlenecks are data quality, distributed training stability, memory, compute, and checkpointing. At inference time, the bottlenecks are KV-cache memory, decode latency, batching efficiency, long prompts, and cost per generated token.
```

### "What are the most important practical tricks?"

```text
The biggest practical wins are high-quality data filtering, deduplication, strong evals, hybrid post-training with SFT and preferences, verifiable rewards for reasoning, distillation, quantization, speculative decoding, continuous batching, prompt/KV caching, routing easy queries to smaller models, and validating outputs with tools or schemas.
```

## 31. Quick Glossary

| Term | Short Meaning |
| --- | --- |
| Autoregressive | generates one token at a time from previous tokens |
| Causal mask | prevents attending to future tokens |
| Cross-entropy | loss used for next-token prediction |
| Teacher forcing | training on true previous tokens |
| SFT | supervised training on ideal responses |
| RLHF | RL from human preferences |
| DPO | direct preference training without explicit reward model |
| RLVR | RL using automatically checkable rewards |
| GRPO | group-relative RL update method |
| MoE | sparse expert architecture |
| GQA | grouped-query attention |
| RoPE | rotary positional embeddings |
| KV cache | cached attention states for decoding |
| FlashAttention | memory-efficient exact attention kernel |
| PagedAttention | paging system for KV cache management |
| Speculative decoding | draft-and-verify faster generation |
| Quantization | lower-precision weights/activations |
| Distillation | smaller model learns from larger model |
| Decontamination | removing benchmark leakage from training data |
| Reward hacking | optimizing reward without solving intended task |
| Test-time compute | spending more inference compute to improve answer quality |

## 32. References

- Transformer foundation: [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
- Early scaling laws: [Scaling Laws for Neural Language Models](https://arxiv.org/abs/2001.08361)
- Chinchilla scaling: [Training Compute-Optimal Large Language Models](https://arxiv.org/abs/2203.15556)
- Llama 3 recipe: [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783)
- DeepSeek-V3 technical report: [DeepSeek-V3 Technical Report](https://arxiv.org/abs/2412.19437)
- DeepSeek-R1 and GRPO/RL reasoning: [DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning](https://arxiv.org/abs/2501.12948)
- Mixtral MoE: [Mixtral of Experts](https://arxiv.org/abs/2401.04088)
- Switch Transformer: [Scaling to Trillion Parameter Models with Simple and Efficient Sparsity](https://arxiv.org/abs/2101.03961)
- RoPE: [RoFormer: Enhanced Transformer with Rotary Position Embedding](https://arxiv.org/abs/2104.09864)
- Grouped-query attention: [GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints](https://arxiv.org/abs/2305.13245)
- FlashAttention: [Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135)
- FlashAttention-2: [Faster Attention with Better Parallelism and Work Partitioning](https://arxiv.org/abs/2307.08691)
- RLHF/InstructGPT: [Training Language Models to Follow Instructions with Human Feedback](https://arxiv.org/abs/2203.02155)
- DPO: [Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- OpenAI reinforcement fine-tuning docs: [Reinforcement fine-tuning](https://platform.openai.com/docs/guides/reinforcement-fine-tuning)
- LoRA: [Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- QLoRA: [Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)
- ZeRO: [ZeRO: Memory Optimizations Toward Training Trillion Parameter Models](https://arxiv.org/abs/1910.02054)
- Megatron-LM: [Efficient Large-Scale Language Model Training on GPU Clusters](https://arxiv.org/abs/2104.04473)
- GPipe: [Easy Scaling with Micro-Batch Pipeline Parallelism](https://arxiv.org/abs/1811.06965)
- vLLM/PagedAttention: [Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)
- Speculative decoding: [Fast Inference from Transformers via Speculative Decoding](https://arxiv.org/abs/2211.17192)
- SmoothQuant: [Accurate and Efficient Post-Training Quantization for Large Language Models](https://arxiv.org/abs/2211.10438)
- AWQ: [Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978)
- Knowledge distillation: [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531)

