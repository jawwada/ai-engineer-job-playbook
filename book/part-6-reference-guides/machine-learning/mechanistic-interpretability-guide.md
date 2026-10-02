# Mechanistic Interpretability: A Complete Guide

Prepared for interview preparation and real system design. Updated May 2026.

Mechanistic interpretability is the attempt to reverse-engineer neural networks into human-understandable mechanisms. For LLMs, that means understanding which internal features, attention heads, MLPs, residual-stream directions, and circuits cause particular model behaviors.

The short version:

```text
Normal evaluation asks: What does the model do?
Mechanistic interpretability asks: How does the model compute that behavior internally?
```

## 1. What Mechanistic Interpretability Is

Mechanistic interpretability, often called mech interp, tries to explain a trained model by identifying the actual computational mechanisms inside it.

It is not just:

- looking at outputs
- asking the model to explain itself
- feature importance on input tokens
- saliency heatmaps
- generic explainable AI dashboards

It is closer to reverse engineering:

```text
Given a trained model and an observed behavior,
find the internal algorithm that produces that behavior.
```

For example:

```text
Behavior:
The model completes "Mary gave John a drink because ___ was thirsty" with "John".

Mechanistic question:
Which heads, MLPs, residual-stream directions, and intermediate representations track the entities and decide the pronoun?
```

## 2. Why It Matters

Mechanistic interpretability is useful for:

- understanding model capabilities
- debugging model failures
- detecting hidden or dangerous behavior
- identifying memorized facts or behaviors
- locating where facts or concepts are represented
- editing or steering model behavior
- building trust in high-stakes systems
- producing stronger safety cases for advanced models
- discovering how neural networks implement algorithms

It matters because behavioral tests are incomplete. A model can pass an eval for the wrong internal reason.

Example:

```text
A model gets arithmetic questions right.
Behavioral eval says: good.
Mechanistic interp asks: is it doing arithmetic, memorizing patterns, using shortcuts, or relying on token-frequency artifacts?
```

## 3. The Central Goal

The central goal is a causal, mechanistic explanation.

A good mechanistic explanation should say:

```text
These internal components represent these features.
These features interact in this order.
This interaction causes the model to produce this output.
If we intervene on the components, the behavior changes as predicted.
```

The word "causal" matters. It is not enough to find a neuron that correlates with a concept. You want to know whether changing that activation changes the model's behavior.

## 4. Mechanistic Interpretability vs Other Explainability

| Approach | What It Explains | Main Limitation |
| --- | --- | --- |
| Behavioral evaluation | input-output performance | does not explain internal cause |
| Prompting model for explanation | model's verbal explanation | may be post-hoc confabulation |
| Attention visualization | attention patterns | attention is not always explanation |
| Feature attribution | input token importance | often not mechanistic |
| Probing | information linearly decodable from activations | information may be present but unused |
| Mechanistic interpretability | internal causal computation | hard, expensive, incomplete |

Mechanistic interpretability tries to move from "the model looked at this token" to "this component moved this information through this path, causing this logit change."

## 5. Transformer Basics Needed For Mech Interp

Most modern LLM mech interp focuses on transformers.

### 5.1 Tokens

Text is split into tokens.

```text
"The capital of France is Paris"
-> ["The", " capital", " of", " France", " is", " Paris"]
```

The model predicts the next token.

### 5.2 Embeddings

Each token becomes a vector.

```text
token id -> embedding vector
```

This vector is the model's initial representation of the token.

### 5.3 Residual Stream

The residual stream is the main information highway of a transformer.

Each layer reads from it and writes updates back into it.

```text
residual stream
  -> attention writes update
  -> MLP writes update
  -> next layer reads updated stream
```

Many mechanistic analyses treat the residual stream as the central workspace where features are represented as directions.

### 5.4 Attention Heads

Attention heads move information between token positions.

They answer:

```text
At this position, which previous positions should I read from?
What information should I copy or transform from them?
```

An attention head has two conceptually different parts:

- QK circuit: decides where to attend
- OV circuit: decides what information to move

QK means query-key. OV means output-value.

### 5.5 MLP Layers

MLPs process information within a token position.

They often behave like feature detectors and feature writers:

```text
if this feature is present:
  write another feature into the residual stream
```

MLPs are important in factual recall, semantic features, and nonlinear transformations.

### 5.6 Logits And Unembedding

The final residual stream is projected to vocabulary logits.

```text
final residual vector -> unembedding matrix -> logits over tokens
```

Higher logit means the model is more likely to output that token.

## 6. Core Vocabulary

| Term | Meaning |
| --- | --- |
| Activation | Internal vector or scalar produced during a model forward pass |
| Component | A part of the model: head, neuron, layer, MLP, residual stream position, feature |
| Feature | A meaningful variable represented inside the model |
| Direction | A vector in activation space associated with a feature |
| Neuron | One scalar dimension in a layer's activation |
| Polysemantic neuron | A neuron that responds to multiple unrelated concepts |
| Monosemantic feature | A feature with one relatively coherent meaning |
| Superposition | Many features represented in overlapping directions in limited dimensions |
| Circuit | A set of components that work together to implement a behavior |
| Head | One attention submodule |
| MLP | Feed-forward submodule in each transformer layer |
| Residual stream | Shared vector workspace passed through layers |
| Logit lens | Project intermediate activations to vocabulary logits |
| Tuned lens | Trained variant of logit lens for more faithful intermediate predictions |
| Activation patching | Replace an activation in one run with activation from another run |
| Causal tracing | Activation-patching style method for locating causal states |
| Path patching | Patch the contribution along a specific path between components |
| Ablation | Remove or zero a component to test its importance |
| Mean ablation | Replace activation with mean activation |
| SAE | Sparse autoencoder, used to decompose activations into sparse features |
| Dictionary learning | Learning a set of basis features that reconstruct activations |
| Attribution graph | Graph of feature interactions contributing to an output |
| Circuit tracing | Building a causal graph of internal computation for a prompt |
| Probe | Classifier trained on activations to test if information is decodable |
| Steering | Intervening on activations to change model behavior |

## 7. What Counts As A Mechanistic Explanation?

A weak explanation:

```text
Head 8.6 activates on names.
```

A stronger explanation:

```text
Head 8.6 attends from the final token to the previous occurrence of the indirect object.
Its OV circuit writes the indirect object's name direction into the residual stream.
Downstream heads read that direction and increase the correct name logit.
Patching this head from a clean run restores the correct answer on corrupted prompts.
Ablating it reduces the correct-answer logit.
```

Mechanistic claims should include:

- what component does
- when it activates
- what information it reads
- what information it writes
- what downstream component uses it
- causal evidence from intervention
- scope of validity

## 8. The Research Mindset

Mechanistic interpretability is hypothesis-driven.

Typical loop:

```text
1. Find a behavior.
2. Build a clean/corrupt input pair.
3. Define a metric.
4. Locate important activations.
5. Form a hypothesis about what they represent.
6. Intervene to test the hypothesis.
7. Build a circuit-level explanation.
8. Validate on new examples.
```

The danger is storytelling. If you only inspect activations and tell a plausible story, you have not proven a mechanism.

Good mech interp work uses interventions.

## 9. Features, Directions, And Representations

### 9.1 The Linear Representation Hypothesis

A common hypothesis is that models represent meaningful features as directions in activation space.

Example:

```text
activation vector
  = base information
  + some amount of "France"
  + some amount of "capital city"
  + some amount of "formal tone"
```

This is not always literally true, but it is useful. Many concepts can be found with linear probes, activation directions, or sparse autoencoder features.

### 9.2 Probing

A probe is a small model trained to predict a property from activations.

Example:

```text
Given residual stream activation,
predict whether the subject is singular or plural.
```

Probing tells you whether information is present.

It does not prove the model uses that information.

Important distinction:

```text
Decodable != causally used.
```

### 9.3 Activation Steering

Activation steering adds or subtracts a feature direction during inference.

Example:

```text
activation = activation + alpha * "positive sentiment direction"
```

If outputs become more positive, that suggests the direction is behaviorally relevant.

But steering is not always mechanistic explanation. It can be useful without fully explaining the circuit.

## 10. Superposition And Polysemanticity

### 10.1 The Problem

Neural networks often represent more features than they have obvious dimensions.

If a layer has 4,096 dimensions, it may still represent far more than 4,096 meaningful concepts.

How?

By superposition:

```text
many sparse features are packed into overlapping directions
```

### 10.2 Why Superposition Happens

Features are often sparse. A feature like "Golden Gate Bridge" appears rarely. A feature like "Python list comprehension" appears in some contexts. A feature like "medical contraindication" appears in others.

If features rarely co-occur, the model can reuse dimensions with limited interference.

This creates polysemantic neurons:

```text
same neuron fires for multiple unrelated concepts
```

### 10.3 Why This Makes Interpretability Hard

If neurons are polysemantic, inspecting individual neurons can mislead you.

A neuron may look like:

```text
fires for French text
fires for legal citations
fires for chess notation
```

The real features may be distributed across combinations of neurons.

This is why sparse autoencoders became central.

## 11. Sparse Autoencoders

Sparse autoencoders, or SAEs, are one of the most important modern tools in mechanistic interpretability.

### 11.1 The Goal

Given model activations, learn a sparse set of features that reconstruct them.

```text
activation vector -> sparse feature activations -> reconstructed activation vector
```

The hope:

```text
messy neuron basis -> cleaner feature basis
```

### 11.2 Basic Architecture

An SAE has:

- encoder: maps activation to feature activations
- sparse bottleneck: only a small number of features active
- decoder: reconstructs original activation

Conceptually:

```text
z = sparse_encoder(x)
x_hat = decoder(z)
```

Where:

- `x` is the original model activation
- `z` is sparse feature activations
- `x_hat` is reconstructed activation

### 11.3 Loss Function

Typical SAE loss:

```text
loss = reconstruction_error + sparsity_penalty
```

Example:

```text
loss = ||x - x_hat||^2 + lambda * ||z||_1
```

The reconstruction term says:

```text
Do not lose model information.
```

The sparsity term says:

```text
Use only a few features per activation.
```

### 11.4 Overcomplete Features

SAEs often have more learned features than the original activation dimension.

Example:

```text
residual stream dimension: 768
SAE features: 24,576
```

This is overcomplete.

Why overcomplete?

Because the model may represent many sparse features in superposition. The SAE tries to unpack them.

### 11.5 What SAE Features Look Like

A feature may activate on:

- a specific person
- a place
- a programming language construct
- legal disclaimers
- unsafe cybersecurity content
- sarcasm
- multilingual versions of the same concept
- refusal-like language
- a mathematical operation
- a sentiment or persona trait

Anthropic and OpenAI both showed that large SAEs can extract millions of interpretable features from frontier-scale models, though many features remain hard to interpret.

### 11.6 SAE Workflow

```text
1. Choose model and layer/hook point.
2. Collect many activations on representative data.
3. Train SAE to reconstruct activations sparsely.
4. Inspect top-activating examples for each feature.
5. Generate a natural-language hypothesis for each feature.
6. Test with held-out examples.
7. Intervene on feature activation to see causal effect.
```

### 11.7 SAE Evaluation

Good SAE features should be:

- sparse
- interpretable
- causally useful
- reconstructive enough to preserve model behavior
- not too split across many duplicate features
- not too broad
- not dead

Common metrics:

| Metric | Meaning |
| --- | --- |
| reconstruction loss | how well SAE reconstructs activation |
| sparsity / L0 | number of active features per token |
| dead feature rate | features that rarely or never activate |
| feature interpretability | how coherent top activations are |
| downstream faithfulness | whether replacing activations with SAE reconstructions preserves behavior |
| intervention effect | whether changing feature activation changes outputs predictably |

### 11.8 SAE Failure Modes

| Failure | Meaning |
| --- | --- |
| dead features | features never activate |
| feature splitting | one concept split across many features |
| feature absorption | one feature absorbs several concepts |
| spurious feature | top examples look coherent, but feature is not causal |
| reconstruction gap | SAE loses information important to model behavior |
| overly broad feature | explanation fits too many unrelated examples |
| basis mismatch | SAE features are not the model's true causal units |

SAEs are powerful, but they are not magic microscopes. They are learned approximations.

## 12. Logit Lens And Tuned Lens

### 12.1 Logit Lens

Logit lens projects intermediate residual-stream activations through the final unembedding matrix.

```text
intermediate residual -> unembedding -> token logits
```

It asks:

```text
If the model had to predict now, what token would it predict?
```

Use it to inspect how predictions evolve layer by layer.

### 12.2 Limitations

The intermediate residual stream is not necessarily in the same "space" as the final residual stream. Early-layer logit lens outputs can be misleading.

### 12.3 Tuned Lens

Tuned lens trains a small translator for each layer before projecting to logits.

```text
layer activation -> learned translator -> unembedding -> logits
```

It often gives more reliable intermediate predictions than raw logit lens.

## 13. Attention Analysis

Attention patterns are visually intuitive but easy to overinterpret.

Attention tells you:

```text
which positions a head reads from
```

It does not by itself tell you:

```text
what information was read
whether that information mattered
how it affected logits
```

Useful attention-head types:

| Head Type | Rough Function |
| --- | --- |
| previous-token head | attends to immediately previous token |
| duplicate-token head | attends to previous occurrence of same token |
| induction head | detects repeated patterns and copies continuation |
| name mover head | moves a name/entity to output position |
| delimiter head | attends to punctuation, separators, or structure tokens |
| retrieval head | attends to relevant context positions |

Attention analysis becomes mechanistic when paired with OV/QK analysis and causal interventions.

## 14. Induction Heads

Induction heads are one of the landmark discoveries in transformer circuits.

They implement a pattern like:

```text
If sequence contains:
A B ... A

Then predict:
B
```

Example:

```text
"... Alice went to the store. Bob stayed home. Alice"
```

An induction head may attend from the second "Alice" to the first "Alice", then copy the token after it.

Why they matter:

- they are a concrete circuit for in-context learning
- they appear across transformer models
- their emergence during training can correspond to phase changes in loss
- they show that transformers learn algorithmic mechanisms, not just memorized facts

## 15. Circuits

A circuit is a set of internal components that implement a behavior.

Examples:

- induction circuit
- indirect object identification circuit
- greater-than circuit
- factual recall circuit
- sentiment classification circuit
- refusal or safety behavior circuit

### 15.1 Circuit Explanation Template

Use this template:

```text
Task:
  What behavior are we explaining?

Metric:
  How do we measure success?

Components:
  Which heads/features/MLPs matter?

Information flow:
  What information moves from where to where?

Causal evidence:
  What patching/ablation proves necessity or sufficiency?

Scope:
  Which examples does this explanation cover?

Limitations:
  What does it not explain?
```

### 15.2 Circuit Quality

A good circuit should be:

- necessary: removing it hurts behavior
- sufficient: using it alone recovers behavior, at least approximately
- specific: it affects the target behavior more than unrelated behaviors
- interpretable: components have meaningful roles
- robust: works across many examples
- predictive: interventions produce expected changes

## 16. Activation Patching

Activation patching is one of the main causal tools.

### 16.1 The Setup

You need:

- clean prompt: model gets answer right
- corrupted prompt: model gets answer wrong
- metric: measures correct behavior

Example:

```text
Clean:
"When Mary and John went to the store, John gave a bottle to Mary. The bottle was given to"
Expected: "Mary"

Corrupt:
"When Mary and John went to the store, Mary gave a bottle to John. The bottle was given to"
Expected: "John"
```

### 16.2 The Intervention

Run both prompts and cache activations.

Then:

```text
During corrupted run,
replace one activation with the corresponding activation from clean run.
Measure whether correct output is restored.
```

If patching a component restores the clean answer, that component likely carries causally relevant information.

### 16.3 What To Patch

You can patch:

- residual stream at layer and token position
- attention head output
- MLP output
- attention pattern
- individual neuron
- SAE feature activation
- path between components

### 16.4 Metrics

Common metric:

```text
logit difference = logit(correct token) - logit(incorrect token)
```

If patching increases logit difference toward clean behavior, the patched activation matters.

### 16.5 Interpretation

Activation patching localizes where information is causally important.

It does not automatically tell you what the component means. You still need interpretation.

## 17. Path Patching

Activation patching asks:

```text
Does this component matter?
```

Path patching asks:

```text
Does this component matter through this specific connection to another component?
```

It isolates an edge in the computational graph.

Use it when:

- many components interact
- you want information-flow structure
- you need to distinguish direct from indirect effects

Path patching is more precise but more complex.

## 18. Causal Tracing

Causal tracing is often used to locate where information is stored or recovered.

Common pattern:

```text
1. Run clean prompt.
2. Corrupt important tokens or activations.
3. Restore activations at selected layers/positions.
4. Identify where restoration recovers the answer.
```

ROME-style work used causal tracing to show that some factual associations are mediated by mid-layer MLP modules at subject-token positions, then moved to output positions by attention.

This led to model editing methods that directly change factual associations.

## 19. Ablation

Ablation removes a component.

Forms:

- zero ablation
- mean ablation
- resample ablation
- feature ablation
- head ablation
- MLP ablation

Question:

```text
If I remove this component, does the behavior break?
```

Risk:

- ablation may create out-of-distribution activations
- a component can be important but redundant
- removing one part may cause broad damage

Mean or resample ablation is often safer than zeroing.

## 20. Attribution Patching

Full activation patching is expensive because it requires many forward passes.

Attribution patching approximates patching effects using gradients.

Idea:

```text
estimated patch effect ≈ activation difference * gradient of metric
```

Pros:

- much faster
- useful for scanning many components

Cons:

- approximation can fail
- should be validated with real patching

## 21. Causal Scrubbing

Causal scrubbing tests whether a proposed explanation is faithful.

Rough idea:

```text
If my hypothesis says these variables are what matter,
then replacing internal activations in ways that preserve those variables
should preserve model behavior.
```

It forces interpretability claims to be precise.

Use it when you have a proposed computational graph or high-level algorithm and want to test whether it truly matches the model.

## 22. Automated Circuit Discovery

Manual circuit discovery is slow.

Automated circuit discovery methods try to find important subgraphs automatically.

Example approach:

```text
start with full computational graph
iteratively remove edges/components
keep parts whose removal changes target metric
return minimal circuit
```

ACDC, Automated Circuit Discovery, is one well-known approach. It has been used to rediscover known circuits in small transformers.

Limitations:

- can depend heavily on metric
- may find brittle circuits
- may miss distributed backup mechanisms
- often still needs human interpretation

## 23. Circuit Tracing And Attribution Graphs

Circuit tracing is a newer direction that tries to generate graph-like explanations for a model's computation on a specific prompt.

Anthropic's 2025 circuit tracing work introduced a pipeline using replacement models and attribution graphs to show how interpretable features influence each other and contribute to an output.

Conceptually:

```text
prompt
  -> identify active features
  -> trace causal interactions between features
  -> build attribution graph
  -> inspect paths leading to output token
```

Attribution graph nodes can represent interpretable features. Edges represent causal influence.

Why this matters:

- moves beyond isolated features
- shows feature-to-feature computation
- can describe multi-step internal reasoning
- helps connect SAEs to circuit-level explanations

Limitations:

- graphs can be huge
- still require interpretation
- replacement models may be imperfect
- causal faithfulness remains an open challenge

## 24. Transcoders And Cross-Layer Transcoders

SAEs reconstruct activations at one point.

Transcoders try to map one internal representation to another, often replacing parts of the model with interpretable feature-level transformations.

Cross-layer transcoders can model how features at one layer lead to features at later layers.

Why they matter:

- they support feature-level computational graphs
- they can help explain interactions across layers
- they are useful for attribution graph construction

Think:

```text
SAE: what features are present here?
Transcoder: how do features here produce features later?
```

## 25. Model Editing As Mechanistic Evidence

Model editing is adjacent to interpretability.

ROME and related methods locate and edit factual associations inside transformer MLP weights.

Example:

```text
Before edit:
"The Eiffel Tower is located in" -> "Paris"

After edit:
"The Eiffel Tower is located in" -> "Rome"
```

Why it matters:

- if editing a localized component changes a specific fact, that supports a mechanistic hypothesis
- it suggests some facts are stored in editable internal mechanisms

But model editing is not always safe:

- edits can have side effects
- facts may be distributed
- specificity/generalization tradeoffs are hard
- editing is not the same as understanding all mechanisms

## 26. Important Case Studies

### 26.1 Vision Circuits

Early mechanistic interpretability work studied vision models such as InceptionV1.

Researchers found circuits for:

- curves
- textures
- object parts
- high-level visual concepts

This established a "circuits" style of analysis before the transformer era.

### 26.2 Induction Heads

Induction heads showed a concrete mechanism for in-context pattern continuation.

They are important because they connect:

- transformer architecture
- attention heads
- training dynamics
- in-context learning

### 26.3 Indirect Object Identification

The IOI task became a classic benchmark for circuit discovery.

Example:

```text
When John and Mary went to the store, John gave a drink to
```

Correct answer:

```text
Mary
```

The IOI circuit includes heads that detect names, move names, suppress wrong names, and coordinate through residual-stream information.

### 26.4 Greater-Than Circuit

Greater-than tasks involve prompts like:

```text
The war lasted from the year 1732 to the year 17
```

The model must prefer years greater than 1732.

Circuit studies show that models can learn specialized mechanisms for numeric comparison patterns.

### 26.5 Factual Recall

Causal tracing and model editing work suggests factual associations can involve:

- subject-token representations
- mid-layer MLP modules
- attention moving retrieved information to final position

This is not the whole story of factual knowledge, but it is a valuable mechanistic handle.

### 26.6 Superposition

Toy models showed how sparse features can be packed into fewer dimensions, explaining why neurons are often polysemantic.

This motivated dictionary learning and sparse autoencoders.

### 26.7 Monosemantic Features In Claude And GPT-4

Anthropic and OpenAI scaled SAEs to large language models and found millions of features that often correspond to meaningful concepts.

Examples include features for:

- entities
- places
- code concepts
- unsafe content
- emotions
- languages
- abstract themes
- multimodal concepts

This is one of the clearest signs that feature-level interpretability can scale beyond toy models.

### 26.8 Circuit Tracing In Claude 3.5 Haiku

Anthropic's 2025 circuit tracing work connected features into attribution graphs for specific prompts, trying to show not just what concepts exist, but how they interact to produce outputs.

This is part of a shift from:

```text
feature discovery
```

to:

```text
feature-level causal computation graphs
```

## 27. Practical Workflow: How To Do A Mech Interp Project

### Step 1: Pick A Narrow Behavior

Bad:

```text
Understand how the model reasons.
```

Good:

```text
Understand how GPT-2 Small solves indirect object identification prompts.
```

Good:

```text
Find which features cause the model to refuse a cybersecurity request.
```

### Step 2: Choose A Model

Start small.

Good beginner models:

- GPT-2 Small
- small Pythia models
- small Gemma models
- toy transformers

Why small:

- cheaper
- easier to patch
- more existing tooling
- easier to inspect circuits

Large models are more realistic but harder.

### Step 3: Build A Dataset

You need many examples of the behavior.

For each example, define:

- prompt
- correct output
- incorrect output
- clean/corrupted pair if patching
- metric

Example:

```json
{
  "clean": "When John and Mary went to the store, John gave a drink to",
  "corrupt": "When John and Mary went to the store, Mary gave a drink to",
  "correct_token": " Mary",
  "incorrect_token": " John"
}
```

### Step 4: Define A Metric

Common:

```text
logit_diff = logit(correct) - logit(incorrect)
```

Other metrics:

- probability of correct token
- loss on target answer
- KL divergence from clean output
- task accuracy
- refusal score
- feature activation

### Step 5: Run Observational Analysis

Inspect:

- attention patterns
- activation norms
- top logits by layer
- logit lens
- neuron activations
- SAE feature activations
- top activating dataset examples

This suggests hypotheses.

### Step 6: Localize With Causal Interventions

Use:

- activation patching
- ablation
- causal tracing
- attribution patching

Goal:

```text
Find which layers, positions, heads, MLPs, or features matter.
```

### Step 7: Interpret Components

For each important component:

- inspect top activating examples
- test synthetic prompts
- study input/output directions
- analyze attention QK and OV behavior
- use SAE feature descriptions
- check downstream effects

### Step 8: Build A Circuit Hypothesis

Write a computational story:

```text
Component A detects X.
Component B moves X to position Y.
Component C suppresses wrong answer.
Component D boosts correct answer logit.
```

### Step 9: Test Necessity And Sufficiency

Necessity:

```text
Remove circuit -> behavior breaks.
```

Sufficiency:

```text
Keep or patch only circuit -> behavior is restored.
```

### Step 10: Validate On New Data

Test:

- more prompts
- adversarial variants
- paraphrases
- different names/entities
- different lengths
- different model sizes

Do not trust a circuit that only works on one prompt.

## 28. Tooling

### 28.1 TransformerLens

TransformerLens is the standard library for many transformer mech interp projects.

It lets you:

- load supported transformer models
- cache activations
- add hooks
- patch activations
- inspect attention heads
- compute logit attribution
- run circuit analysis

Best for:

- GPT-style open models
- educational work
- classic circuit analysis
- activation patching

### 28.2 NNsight

NNsight provides tracing and intervention tools for neural networks, including large transformer models.

It is useful when:

- working with Hugging Face models
- tracing internal activations
- doing interventions
- using remote execution infrastructure

### 28.3 SAELens

SAELens supports sparse autoencoder work.

Use it for:

- training SAEs
- loading pretrained SAEs
- analyzing SAE features
- feature activation inspection

### 28.4 Neuronpedia

Neuronpedia is a browser for neurons, SAE features, and interpretability artifacts.

Use it to:

- inspect top activating examples
- browse SAE features
- compare feature explanations
- explore attribution/circuit artifacts

### 28.5 Circuit Tracer

Anthropic has open-sourced circuit-tracing tools that can generate attribution graphs for supported open-weight models and explore them interactively.

Use it for:

- feature-level graph explanations
- prompt-specific circuit tracing
- interactive causal graph exploration

## 29. Minimal Code Concepts

This is pseudocode, not a full script.

### 29.1 Cache Activations

```python
logits, cache = model.run_with_cache(prompt)
resid = cache["resid_post", layer]
attn = cache["pattern", layer]
mlp = cache["mlp_out", layer]
```

### 29.2 Logit Difference Metric

```python
def logit_diff(logits, correct_token, incorrect_token):
    final_logits = logits[0, -1]
    return final_logits[correct_token] - final_logits[incorrect_token]
```

### 29.3 Activation Patching

```python
clean_logits, clean_cache = model.run_with_cache(clean_prompt)
corrupt_logits, corrupt_cache = model.run_with_cache(corrupt_prompt)

def patch_hook(corrupt_activation, hook):
    corrupt_activation[:, position, :] = clean_cache[hook.name][:, position, :]
    return corrupt_activation

patched_logits = model.run_with_hooks(
    corrupt_prompt,
    fwd_hooks=[("blocks.5.hook_resid_post", patch_hook)]
)
```

### 29.4 Feature Steering

```python
def steering_hook(activation, hook):
    activation[:, :, :] += alpha * feature_direction
    return activation
```

## 30. How To Read A Mechanistic Interpretability Paper

Ask:

1. What behavior is being explained?
2. What model and dataset are used?
3. What metric defines success?
4. What components are claimed to matter?
5. Is evidence causal or only correlational?
6. Are clean/corrupt pairs well designed?
7. Are ablations out-of-distribution?
8. Is the circuit necessary?
9. Is the circuit sufficient?
10. Does it generalize beyond cherry-picked examples?
11. Are alternative explanations ruled out?
12. Are tools or datasets released?

## 31. Common Mistakes

- Treating attention as explanation.
- Treating probes as proof of model use.
- Interpreting individual neurons despite superposition.
- Ignoring causal interventions.
- Using one prompt and overgeneralizing.
- Choosing a metric that does not match the behavior.
- Confusing feature steering with full mechanistic understanding.
- Ignoring SAE reconstruction error.
- Assuming a found circuit is the only circuit.
- Ignoring backup circuits or redundancy.
- Making anthropomorphic claims about model "thoughts" beyond evidence.

## 32. Limitations Of The Field

Mechanistic interpretability is promising but incomplete.

Current limitations:

- frontier models are huge
- circuits can be distributed and messy
- SAEs are imperfect approximations
- feature explanations may be too broad
- many features remain uninterpretable
- causal graphs can be enormous
- interpretations are often local to a prompt/task
- tools can be architecture-specific
- safety-relevant features may be rare or hidden
- models may change across fine-tuning or context

Important caution:

```text
Mechanistic interpretability is not yet a complete safety solution.
```

It is a scientific and engineering tool that can improve understanding, debugging, and monitoring.

## 33. SOTA Direction As Of 2026

The field is moving from:

```text
single neurons
```

to:

```text
features, circuits, and causal graphs
```

Major directions:

| Direction | Meaning |
| --- | --- |
| sparse autoencoders at scale | extracting millions of features from large models |
| feature steering | controlling behavior through interpretable feature interventions |
| sparse feature circuits | finding causal graphs over SAE features |
| circuit tracing | producing attribution graphs for prompt-specific computations |
| automated interpretation | using models to label features or describe graphs |
| multimodal mech interp | applying methods to vision-language, diffusion, audio, and robotics models |
| formal causal abstraction | making mechanistic claims mathematically precise |
| mechanistic data attribution | tracing circuits/features back to training data |
| safety monitoring | looking for deception, hidden objectives, jailbreak features, or dangerous capabilities |

The big unsolved question:

```text
Can we scale mechanistic interpretability from local explanations of small behaviors to reliable auditing of frontier models?
```

## 34. Learning Path

### Stage 1: Foundations

Learn:

- transformer architecture
- attention
- residual stream
- logits/unembedding
- basic PyTorch
- linear algebra

### Stage 2: Classic Tools

Practice:

- logit lens
- attention visualization
- activation caching
- head ablation
- activation patching

### Stage 3: Circuits

Study:

- induction heads
- IOI circuit
- greater-than circuit
- factual recall / ROME
- automated circuit discovery

### Stage 4: SAEs

Learn:

- superposition
- sparse autoencoders
- dictionary learning
- feature inspection
- feature steering
- SAE failure modes

### Stage 5: Modern Frontier

Study:

- scaling monosemanticity
- GPT-4/Claude feature extraction
- sparse feature circuits
- circuit tracing
- attribution graphs
- automated graph descriptions

## 35. Interview-Ready Answers

### "What is mechanistic interpretability?"

```text
Mechanistic interpretability is the attempt to reverse-engineer a neural network's internal computation into human-understandable mechanisms. For transformers, that usually means identifying features, attention heads, MLPs, residual-stream directions, and circuits that causally produce a behavior.
```

### "How is it different from normal explainability?"

```text
Most explainability methods are correlational or input-focused: saliency, attention maps, probes, or model-generated explanations. Mechanistic interpretability aims for causal internal explanations. It asks which internal components represent what information, how they interact, and whether intervening on them changes behavior as predicted.
```

### "What is superposition?"

```text
Superposition is the idea that models represent more features than they have clean dimensions by packing sparse features into overlapping directions. This makes individual neurons polysemantic and motivates sparse autoencoders, which try to recover a more interpretable feature basis.
```

### "What is an SAE?"

```text
A sparse autoencoder is trained on model activations to reconstruct them using a sparse set of learned features. Because only a few features activate for each token and the feature space is overcomplete, SAEs can sometimes unpack polysemantic neuron activations into more monosemantic, human-interpretable features.
```

### "What is activation patching?"

```text
Activation patching is a causal intervention. You run a clean prompt where the model behaves correctly and a corrupted prompt where it fails, then replace one internal activation in the corrupted run with the corresponding clean activation. If this restores the correct output, that activation likely carries causally important information.
```

### "What is a circuit?"

```text
A circuit is a group of model components that jointly implement a behavior. A strong circuit explanation identifies what each component represents or moves, how information flows between them, and proves the circuit is necessary or sufficient through ablations and patching.
```

### "Why is attention not explanation?"

```text
Attention shows which positions a head reads from, but not what information is read, whether it matters, or how it affects the output. It becomes mechanistically meaningful only when connected to OV/QK behavior and causal interventions.
```

## 36. Quick Glossary

| Term | Short Meaning |
| --- | --- |
| Mechanistic interpretability | reverse-engineering model internals |
| Circuit | internal components implementing a behavior |
| Feature | meaningful represented variable |
| Neuron | scalar activation dimension |
| Polysemanticity | one neuron represents multiple concepts |
| Monosemanticity | one feature has one coherent meaning |
| Superposition | overlapping representation of many sparse features |
| Residual stream | transformer information highway |
| Attention head | component that moves information across positions |
| QK circuit | decides attention pattern |
| OV circuit | decides what information is written |
| MLP | per-position nonlinear feature processor |
| Logit lens | projects intermediate activations to token logits |
| Activation patching | causal activation replacement |
| Path patching | causal test of a component-to-component path |
| Ablation | removing or replacing a component |
| SAE | sparse autoencoder for feature discovery |
| Transcoder | interpretable mapping between internal representations |
| Attribution graph | graph of feature interactions causing output |
| Causal tracing | intervention method for locating causal states |
| ACDC | automated circuit discovery method |
| Steering | changing activations to alter behavior |

## 37. References

- Transformer Circuits framework: [A Mathematical Framework for Transformer Circuits](https://transformer-circuits.pub/2021/framework/index.html)
- Induction heads: [In-context Learning and Induction Heads](https://transformer-circuits.pub/2022/in-context-learning-and-induction-heads/index.html)
- Toy models of superposition: [Toy Models of Superposition](https://arxiv.org/abs/2209.10652)
- Sparse autoencoders in language models: [Sparse Autoencoders Find Highly Interpretable Features in Language Models](https://arxiv.org/abs/2309.08600)
- Anthropic monosemanticity: [Towards Monosemanticity](https://transformer-circuits.pub/2023/monosemantic-features/index.html)
- Anthropic scaling monosemanticity: [Scaling Monosemanticity](https://transformer-circuits.pub/2024/scaling-monosemanticity/index.html)
- Anthropic mapping large model features: [Mapping the Mind of a Large Language Model](https://www.anthropic.com/research/mapping-mind-language-model)
- OpenAI sparse autoencoders: [Extracting Concepts from GPT-4](https://openai.com/index/extracting-concepts-from-gpt-4/)
- OpenAI SAE paper: [Scaling and Evaluating Sparse Autoencoders](https://arxiv.org/abs/2406.04093)
- Circuit tracing: [Circuit Tracing: Revealing Computational Graphs in Language Models](https://transformer-circuits.pub/2025/attribution-graphs/methods.html)
- Attention feature interactions: [Tracing Attention Computation Through Feature Interactions](https://transformer-circuits.pub/2025/attention-qk/index.html)
- ROME and causal tracing: [Locating and Editing Factual Associations in GPT](https://arxiv.org/abs/2202.05262)
- Automated circuit discovery: [Towards Automated Circuit Discovery for Mechanistic Interpretability](https://arxiv.org/abs/2304.14997)
- Causal abstraction: [Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability](https://arxiv.org/abs/2301.04709)
- Tuned lens: [Eliciting Latent Predictions from Transformers with the Tuned Lens](https://arxiv.org/abs/2303.08112)
- Linear representation hypothesis: [The Linear Representation Hypothesis and the Geometry of Large Language Models](https://arxiv.org/abs/2311.03658)
- TransformerLens: [TransformerLens GitHub](https://github.com/TransformerLensOrg/TransformerLens)
- NNsight: [NNsight documentation](https://nnsight.net/documentation/)
- Neuronpedia: [Sparse Autoencoder docs](https://docs.neuronpedia.org/sparse-autoencoder)
- Anthropic circuit tracing tools: [Open-sourcing circuit tracing tools](https://www.anthropic.com/research/open-source-circuit-tracing)

