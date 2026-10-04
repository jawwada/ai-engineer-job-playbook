# 17. Beyond LLMs: the model families you will be asked about

> **What you need to be able to say:** what each family is for, how it is trained in one sentence, and where it sits next to an LLM in a real system. Transformers did not replace everything — ranking, forecasting, anomaly detection, vision and audio each have their own workhorses, and AI-engineer interviews drift into them the moment your resume mentions one.

## 17.1 The map of families

| Family | Learns to… | Typical models | Where it shows up in an AI system |
|---|---|---|---|
| Autoregressive transformers (LLMs) | predict the next token | Claude, GPT, Gemini, Llama, Qwen | reasoning, generation, tool use, orchestration |
| Encoder transformers | produce representations | BERT family, embedding models, rerankers | retrieval, classification, deduplication |
| Vision transformers and CNNs | represent images | ViT, SigLIP, CLIP, SAM, ResNet, YOLO | OCR, document understanding, inspection, search |
| Audio models | represent and generate sound | Whisper, Audio Spectrogram Transformer (AST), wav2vec 2.0, Nova Sonic, ElevenLabs | speech-to-text, text-to-speech, audio tagging, voice agents |
| Diffusion and flow models | denoise toward data | Stable Diffusion/SDXL, FLUX, Imagen, Veo, Sora | image/video generation, inpainting, synthetic data |
| Joint-embedding predictive (JEPA) and world models | predict in representation space | I-JEPA, V-JEPA 2, Genie, Dreamer | robotics, video understanding, planning |
| State-space and hybrid sequence models | model long sequences linearly | Mamba, Jamba, Hyena, RWKV | long-context and on-device sequence tasks |
| Recommendation and ranking | score candidates | two-tower retrieval, DLRM, DCN, cross-encoders, LambdaMART | search, feeds, ads, candidate scoring |
| Gradient-boosted trees | fit tabular data | XGBoost, LightGBM, CatBoost | churn, risk, pricing, fraud, almost every tabular problem |
| Time-series models | forecast | NeuralProphet, Prophet, TFT, N-BEATS, DeepAR, Chronos, TimesFM | demand, load, pricing, capacity |
| Autoencoders and VAEs | compress and reconstruct | AE, VAE, VQ-VAE | anomaly detection, latent spaces for diffusion |
| Graph neural networks | pass messages over graphs | GCN, GraphSAGE, GAT | fraud rings, knowledge-graph completion, molecules |
| Reinforcement learning | optimize a policy | PPO, GRPO, DPO (for LLMs), SAC | LLM post-training, control, bidding |
| Vision-language-action (VLA) | map pixels and text to actions | RT-2, OpenVLA, π0, Gemini Robotics | robotics; the frontier of "agents in the physical world" |

## 17.2 Transformers and attention, in one page

A transformer maps a sequence of tokens to a sequence of vectors through stacked blocks of *self-attention* (each token mixes information from the others, weighted by learned query–key similarity) and *feed-forward* layers, with residual connections and normalization. Decoder-only models (all LLMs) attend only to earlier tokens and are trained to predict the next one on trillions of tokens; encoder-only models (BERT, embedding models) attend both ways and are trained with masked tokens or contrastive objectives; encoder–decoder models (T5, Whisper's architecture) encode an input and decode an output. Attention costs grow with the square of the sequence length at training and prefill time, and decoding is memory-bound on the KV cache (every generated token re-reads the keys and values of everything before it), which is why KV caches, grouped-query attention, multi-head latent attention (DeepSeek's low-rank KV compression), sliding windows, FlashAttention, mixture-of-experts feed-forward layers and the state-space alternatives exist. Two details interviewers probe: positional information comes from rotary embeddings (RoPE), and "extending the context" means retraining or rescaling those frequencies, which is why long-context quality is not free; and the output layer is a softmax over a 100k–250k-token vocabulary, so sampling settings (temperature, top-p, min-p) and structured-output constraints act at that layer. Post-training turns a base model into an assistant: supervised fine-tuning on demonstrations, then preference optimization (RLHF with PPO, or direct methods such as DPO) and, for reasoning models, reinforcement learning with verifiable rewards (GRPO-style) on math, code and tool-use tasks. Chapter 26 covers the training you might do yourself; chapter 26b the full post-training pipeline.

## 17.3 Vision: ViT, CLIP/SigLIP, SAM and document models

A **Vision Transformer (ViT)** cuts an image into patches (16×16 pixels), embeds each as a token and runs a transformer over them; it replaced CNNs as the backbone for most new work when enough data is available, while **CNNs** (ResNet, EfficientNet, YOLO for detection) remain efficient for edge and small-data cases. **CLIP** and **SigLIP** train an image encoder and a text encoder so matching pairs are close in one embedding space, which gives zero-shot classification and image–text search and is the vision half of most multimodal LLMs. **SAM** segments anything from a prompt (point, box, text). **Document AI** stacks (Azure Document Intelligence, Google Document AI, Textract, Docling, LayoutLM-style models and now multimodal LLMs directly) turn PDFs and scans into structured text, tables and key-value pairs — the first step of most enterprise RAG. **Semantic segmentation** labels every pixel (U-Net, DeepLab, SegFormer); it is what drone-inspection and medical-imaging pipelines run.

## 17.4 Audio: from spectrograms to speech-to-speech

Audio is handled as a **spectrogram** (time × frequency image), which is why image architectures transfer: the **Audio Spectrogram Transformer (AST)** is a ViT over mel-spectrograms for audio tagging and event detection. **Speech-to-text** (ASR) models — Whisper and its distilled/turbo variants, wav2vec 2.0, Conformer models behind Deepgram, AssemblyAI and the cloud speech APIs — map audio to text with timestamps and diarization. **Text-to-speech** (ElevenLabs, Cartesia, OpenAI TTS, Google and Amazon Polly/Nova) maps text to a waveform with controllable voice and prosody. **Speech-to-speech** models (Amazon Nova Sonic, Gemini Live, OpenAI Realtime, Moshi) take audio in and produce audio out in one model, cutting the 1–2 s latency of the ASR → LLM → TTS chain to a few hundred milliseconds and preserving tone; the chain survives where you need control, logging and cheaper components. Chapter 41 designs a voice agent end to end.

## 17.5 Diffusion and flow-matching models

A diffusion model learns to reverse a noising process: train it to predict the noise added to an image (or a latent code of it) at a random step, then generate by starting from pure noise and denoising step by step, guided by a text embedding (classifier-free guidance). **Latent diffusion** (Stable Diffusion, SDXL, FLUX) runs in the compressed latent space of a VAE, which makes it affordable; **flow matching** and rectified flows are the 2024–26 refinement with straighter paths and fewer steps; the frontier labs now also generate images *autoregressively or natively inside the multimodal LLM* (GPT image models, Gemini's "Nano Banana" image models), which is why text rendering and instruction-following in images improved so sharply; **video models** (Veo, Sora, Wan) add temporal attention over frames; **ControlNet, LoRA adapters, IP-Adapter** add conditioning (edges, poses, a reference style); **inpainting and outpainting** edit regions. In production the engineering questions are GPU cost per image, step count versus quality (distilled few-step models), safety filtering of prompts and outputs, and provenance (watermarks such as SynthID, C2PA metadata).

## 17.6 JEPA and world models

The **Joint-Embedding Predictive Architecture (JEPA)**, Yann LeCun's proposal for self-supervised learning, predicts in *representation space* rather than in pixels: an encoder embeds the visible part of an input, a predictor forecasts the embedding of the masked part, and a slowly updated (EMA) target encoder, which receives no gradient, provides the targets. That asymmetry keeps training from collapsing to trivial outputs in practice, but an EMA target alone does not guarantee it: the theory is partial, and the quieter dimensional collapse still has to be monitored (17b.1.5). The point is to spend capacity on structure that is predictable — object permanence, motion, physics — and ignore unpredictable detail (leaves, ripples) that a pixel-level generative model is forced to render. **I-JEPA** (images, 2023) and **V-JEPA** (video, 2024) showed strong representations without labels; **V-JEPA 2** (June 2025) scaled this to over a million hours of video with a ViT encoder over spatio-temporal "tubelets", then post-trained a new action-conditioned predictor (**V-JEPA 2-AC**, about 300M parameters) on top of the frozen encoder with under 62 hours of unlabeled robot video, so that a robot can plan by imagining the embedding of the future under candidate actions and picking the sequence that lands closest to the embedding of a goal image — model-predictive control, zero-shot in two labs not seen in training. **World models** more broadly (DreamerV3, Genie 3, Cosmos) learn simulators of an environment, in pixels or in latents, that an agent can plan in; they are the physical-world counterpart of the reasoning that LLM agents do in text. Why this matters for an AI-engineer interview: it is the standard "what is beyond next-token prediction" question, and the honest answer is that language agents and world-model agents are converging on the same loop — perceive, predict, act, correct — with different substrates. Chapter 17b covers JEPA, world models and joint-embedding architectures in depth: the JEPA family model by model, the adjacent models, practical use today, JEPA versus LLMs for agents, and interview questions with model answers.

## 17.7 State-space models and hybrids

**Mamba** and its successors replace attention with a selective state-space recurrence: linear time in sequence length, constant memory per step at inference, and competitive quality at small and medium scale; **Jamba** and several 2025–26 hybrids interleave a few attention layers with many state-space or linear-attention layers to recover attention's precision on retrieval-like tasks while keeping most of the efficiency — IBM's Granite 4.0 (Mamba-2 hybrid), NVIDIA's Nemotron-H, and Alibaba's Qwen3-Next (Gated DeltaNet layers in a 3:1 ratio with attention, plus a very sparse MoE) are the production examples to name. The honest trade-off: pure recurrent models compress history into a fixed-size state, so exact recall of a specific earlier token (a part number on page 400) is worse than attention's; hybrids keep a few attention layers precisely to fix that. They matter for very long inputs (logs, genomes, audio) and for edge devices, and they are a good answer to "how would you handle a 10-million-token context" — alongside the pragmatic answer, which is retrieval.

## 17.8 Ranking and recommendation

The pattern behind search, feeds and ads is **retrieve-then-rank**: a cheap stage pulls a few hundred candidates from millions (a **two-tower model** embeds users and items separately so retrieval is a nearest-neighbor lookup; or BM25; or a graph walk), then a richer model scores each candidate with full cross-features (a **cross-encoder** or a deep CTR model such as DLRM/DCN with embedding tables for categorical features), then a final stage applies business rules, diversity and calibration. Serving at thousands of queries per second means feature stores, precomputed item embeddings, approximate nearest-neighbor indexes, and online learning with daily or hourly updates. Evaluation is offline (AUC, NDCG, log-loss, calibration) and online (A/B tests with statistical gates and rollback). LLM-era additions: LLM-generated item descriptions and user summaries as features, LLM rerankers for small candidate sets, and conversational recommendation.

## 17.9 Tabular, forecasting and anomaly detection

**Gradient-boosted trees** (XGBoost, LightGBM, CatBoost) remain the best default on tabular business data — churn, propensity, risk, pricing, fraud — with SHAP for explanations and careful leakage control; the LLM-era challenger is **TabPFN** (a transformer pre-trained on synthetic tabular tasks that predicts in one forward pass and leads on small datasets, under ~10k rows), and the honest comparison is "GBDT with tuned features still wins at scale, TabPFN wins on small and fast". **Forecasting** spans classical (ARIMA, exponential smoothing), decomposable (Prophet, **NeuralProphet** — trend + seasonality + holidays + autoregression with a neural layer), deep (Temporal Fusion Transformer, N-BEATS, DeepAR) and the **time-series foundation models** (Chronos and Chronos-2, TimesFM 2.x, Moirai, TabPFN-TS) that forecast zero-shot and are now the right first baseline; the hard parts are hierarchy and reconciliation, intermittent demand, covariates (promotions, weather) that the zero-shot models handle unevenly, and evaluating with the right horizon and metric (MAPE, WAPE, pinball loss for quantiles) against a seasonal-naive baseline that you must beat before claiming anything. **Anomaly detection** uses reconstruction error from **autoencoders/VAEs**, isolation forests, forecasting residuals, or density models; the production question is always the threshold and the alert budget — set the threshold from the number of alerts an operator can act on per shift, not from a p-value.

## 17.10 Reinforcement learning, briefly

RL optimizes a policy to maximize reward from an environment. In the LLM world it appears as RLHF (a reward model trained on human preferences; PPO updates the policy), **DPO** (skip the reward model; optimize directly on preference pairs), and **GRPO**-style RL with verifiable rewards (math/code correctness, test passes, tool-use success) that produced the reasoning models. In classic settings it runs bidding, control and recommendation exploration (bandits). The practical vocabulary: reward hacking, KL penalties to stay near the reference model, on-policy versus off-policy, and why evals must be held out from the reward.

## 17.11 Vision-language-action and robotics

VLA models fine-tune a vision-language model to emit robot actions as tokens (RT-2, OpenVLA, π0, Gemini Robotics), trained on teleoperation datasets (Open X-Embodiment, DROID). Combined with world models (17.6) and simulation, this is where "agents" meet hardware. For a software AI engineer the relevance is conceptual: the same stack of perception, planning, tool calls and safety constraints applies.

## 17.12 How the families combine in one real system

A customer-service voice agent: ASR (audio family) → LLM with tools (transformer) → retrieval with embeddings and a reranker (encoder family) over documents parsed by a document model (vision family) → TTS (audio) — plus a gradient-boosted model scoring churn risk from the CRM to decide when to escalate, and a forecasting model sizing the call-center staffing the agent is deflecting. Being able to draw that in an interview is worth more than knowing any single architecture in depth.

### The cost and latency envelope of each family

The reason systems combine families this way is economics, and interviewers expect you to know the orders of magnitude. Per inference, on 2026 hardware and typical sizes (treat as ranges, not quotes):

| Family | Latency per call | Cost per 1,000 calls | Where it runs |
|---|---|---|---|
| GBDT classifier/regressor | microseconds–1 ms | fractions of a cent | CPU, inside the request path |
| Embedding model (text, 500 tokens) | 5–50 ms | \$0.01–0.10 (API) | CPU or small GPU, batched |
| Cross-encoder reranker (50 pairs) | 50–300 ms | \$1–2 (hosted) | GPU |
| CNN/ViT classifier or segmenter | 2–30 ms | cents | GPU, or CPU/edge for small CNNs |
| ASR, streaming | 200–500 ms to final transcript | \$5–10 per 1,000 minutes | GPU or API |
| TTS, streaming | 100–300 ms to first audio | \$10–30 per 1,000 minutes | API |
| Speech-to-speech model | 300–600 ms turn latency | billed per audio minute | API |
| LLM, cheap tier (1k in / 200 out) | 0.5–2 s | \$1–3 | API |
| LLM, frontier tier with 4k thinking | 10–60 s | \$50–300 | API |
| Diffusion image (1024², ~25 steps) | 1–5 s | \$10–40 | GPU |

Read the table bottom-up when designing: every call you can move from an LLM row to a classifier, embedding or rule row is a 100–1,000× saving, which is the whole argument for routing, distillation and "deterministic where deterministic".
