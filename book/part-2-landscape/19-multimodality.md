# 19. Multimodality: what it is, how it works, when to use it

> **What you need to be able to say:** what "native multimodal" means versus a vision encoder bolted onto an LLM; how images, audio and video become tokens and what they cost; the four production patterns (document understanding, visual search, voice, video analysis); and when a multimodal LLM beats a specialized model. Scenarios at the end tie it to real projects, including the film/sound and drone-imagery work on the resume in Part 5.

## 19.1 Definitions

A **modality** is a type of input or output: text, image, audio, video, structured data, sensor streams. A **multimodal model** consumes or produces more than one. Two architectures exist:

1. **Encoder + projector + LLM** (LLaVA, early GPT-4V-style systems, most open VLMs until 2024): a frozen or lightly tuned vision encoder (ViT/SigLIP) turns an image into a few hundred patch embeddings; a small projector maps them into the LLM's token space; the LLM reads them as if they were words. Cheap to build from existing parts, limited at fine-grained spatial and text-in-image tasks unless the encoder is high-resolution and tiled.
2. **Natively multimodal / early fusion** (Gemini, GPT-4o lineage, Claude, Llama 4, Qwen-VL/Omni, Nova): one network trained from the start on interleaved text, image, audio and video tokens, often with the ability to *generate* images or audio as well. Better grounding, longer multimodal context (hour-long video, large PDFs), speech-to-speech with intonation, but opaque and expensive to train — you consume these through APIs.

Images are tokenized into patches (a 1024×1024 image is on the order of 1,000–1,600 tokens depending on the vendor; providers tile large images), audio into roughly 25–50 tokens per second on native models (or into text via ASR in the chained pattern), video into sampled frames (about 1 frame/second, each a few hundred tokens) plus the audio track. The vendor formulas, as of 2026 (verify — they change with model versions): Claude bills an image at about (width × height) ÷ 750 tokens and downsizes anything over ~1.15 megapixels, so a full page is ~1,500 tokens; Gemini charges a flat 258 tokens for images up to 384 px and tiles larger ones into 768×768 crops at 258 each, audio at 32 tokens per second and video at roughly 263 tokens per second at the default frame rate; OpenAI's GPT lineage uses a base charge plus a per-512-px-tile charge in "high detail" mode and a flat low-detail charge. Cost follows token count: a 20-page scanned PDF as images can be 30,000 input tokens; the same PDF as extracted text is 10,000, and an hour of video is on the order of a million tokens. That arithmetic decides most architectures — and it is also why prompt caching matters for multimodal: a long reference document or image set in the prefix is cached like any other tokens.

## 19.2 The four production patterns

**1. Document understanding.** Invoices, claims, contracts, lab reports, slides. Options: (a) OCR/layout pipeline (Azure Document Intelligence, Google Document AI, Textract, Docling) to text and tables, then an LLM for extraction and reasoning; (b) send page images straight to a multimodal LLM with a JSON schema; (c) hybrid — layout model for tables and coordinates, LLM for semantics. Pattern (a) is cheaper and auditable (bounding boxes, confidence per field; the cloud OCR services cost roughly \$1–1.50 per 1,000 pages for text and \$10–65 per 1,000 for prebuilt invoice or custom models) and lets you check whether a PDF already has a text layer, which skips OCR entirely; (b) handles handwriting, stamps, charts and messy layouts better and is faster to build, at ~1,500 tokens per page and with no per-field confidence unless you ask the model to self-report one (which is poorly calibrated); (c) is what regulated deployments converge on. Always validate extracted fields against business rules (totals add up, dates in range, IDs match a checksum) and keep the page image for human review. The failure modes that text-only evals never catch: digit transposition in amounts, rotated or skewed scans, tables split across tiles, checkboxes read as text, and multi-column layouts read in the wrong order.

**2. Visual search and retrieval.** Multimodal embeddings (chapter 18) or page-image late-interaction models (ColPali) index screenshots, product photos, slides and charts; queries are text or images. This is the backbone of "find the slide where we showed the churn chart" and of e-commerce similar-item search.

**3. Voice and audio.** Chained (ASR → LLM → TTS) versus native speech-to-speech; audio classification and tagging with spectrogram models (AST, CLAP); music and sound generation (MusicGen, Stable Audio, MMAudio-style video-to-audio). Chapter 41 designs a voice agent; chapter 17 covers the model families.

**4. Video and streams.** Long-context native models summarize meetings, index footage, detect events and answer questions over hours of video (an hour at Gemini's default sampling is roughly a million tokens — about \$0.75 on a Flash tier, \$2–4 on Pro, before caching); cheaper pipelines sample keyframes, run a vision model per frame and aggregate; real-time streams (Gemini Live, OpenAI Realtime, custom WebRTC with frame sampling) power assistants that "see" a screen or a camera. Google's 2026 lineup also includes "Omni" models that take text, image, video and audio in one request and can emit video, and dedicated transcription models billed per audio minute — check the pricing page rather than assuming one price per modality.

## 19.3 Generation: images, audio, video

Diffusion and flow models (Stable Diffusion/SDXL, FLUX, Imagen, GPT image models, Veo, Sora, Wan) generate from text and references; LoRA adapters personalize style and characters; ControlNet-style conditioning constrains layout; inpainting edits. Production concerns: GPU seconds per asset, licensing of training data and outputs, brand safety filters on prompts and outputs, watermarking (SynthID, C2PA), and human review for anything customer-facing. In film and sound production the valuable workflows are previsualization, asset variations, automatic dialogue replacement, and video-to-audio (foley) generation — all of which need a human-in-the-loop review stage and versioned assets.

## 19.4 Multimodal RAG and agents

A multimodal RAG system indexes text chunks *and* images/pages, retrieves both, and sends the relevant page images plus text to a multimodal LLM; it cites page numbers and regions. Multimodal agents add tools: a chart-reading step, OCR on demand, a screenshot of a web page (computer use), a camera frame. Evaluation must include visual questions ("what does the dashed line represent in figure 3?") because text-only evals will not catch regressions in the vision path. Evaluating and securing that path comes down to five habits:

- **Build a visual eval set** of 50–100 items with the real failure classes: rotated scans, low resolution (fax-quality), handwriting, charts without axis labels, tables with merged cells, multi-column text, screenshots with pop-ups. Score field-level accuracy, not "looks right".
- **Measure the resolution budget.** Downscaling is where accuracy silently dies: a 300-dpi page downsized to 1,000 px makes 8-point text unreadable. Decide crop/tile strategy per document type and test it.
- **Treat images as untrusted input.** Text inside an image is a prompt-injection channel (instructions printed on an invoice or rendered in a screenshot); the same rules as for tool output apply (chapter 30), and computer-use agents are the most exposed.
- **Calibrate confidence.** Models are over-confident about what they read; where a decision depends on a field, route low-agreement cases (two models or model-versus-OCR disagree) to a human rather than trusting a self-reported score.
- **Cost per document** is the metric that decides pattern (a) versus (b): compute it on the real page mix before choosing.

## 19.5 When multimodal beats a specialized model — and when it does not

| Situation | Prefer | Why |
|---|---|---|
| Open-ended questions about mixed documents | multimodal LLM | reasoning across layout, charts and text |
| High-volume, fixed-schema extraction (10M invoices/year) | OCR/layout model + small LLM, or a fine-tuned document model | 10–50× cheaper, confidence scores, bounding boxes |
| Defect detection on a production line | CNN/ViT classifier or segmentation model | latency in milliseconds, deterministic, trainable on your defects |
| Semantic search over slides and screenshots | multimodal embeddings / ColPali | no parsing, visual layout preserved |
| Real-time voice with emotion | native speech-to-speech | 300–600 ms turn latency, prosody |
| Voice with strict control and logging | chained ASR→LLM→TTS | inspectable transcripts, cheaper, swappable parts |
| Audio event tagging (gunshot, glass, siren) | spectrogram transformer (AST) | small, fast, trainable on labeled clips |

## 19.6 Scenarios (use-case driven)

- **Claims intake at an insurer.** Photos of damage plus a PDF form plus a voicemail. Pipeline: ASR on the voicemail; Document Intelligence on the form with field confidence; a multimodal LLM reads the photos against the claim type and the form to flag inconsistencies; a rules layer decides straight-through processing versus adjuster review. Metrics: straight-through rate, false-approval rate, time to decision.
- **Film and sound production (resume use case).** Multimodal retrieval over footage and takes (video embeddings + transcripts), ViT-based scene/shot classification, Audio Spectrogram Transformer tagging of sound events, Stable Diffusion for concept art variants, generated foley via video-to-audio models, all behind an agentic workflow with human review and versioning; served on GPU/TPU with batching. The engineering story is throughput (batch size, mixed precision, model serving on GKE or the Gemini Enterprise Agent Platform, formerly Vertex AI) and the review loop, not the models.
- **Utility asset inspection from drones (resume use case).** Semantic segmentation (CNN/U-Net family or SegFormer) on drone imagery to find corrosion, vegetation encroachment and damaged insulators; geospatial scoring joins detections to asset registries (PostGIS); a multimodal LLM writes the inspection report from the detections and reference images; humans validate before work orders are raised.
- **Retail product catalog enrichment.** Multimodal LLM reads product photos and supplier PDFs to fill attributes; multimodal embeddings power "similar items"; a small classifier flags policy-violating images; A/B test conversion.
- **Meeting intelligence.** Native long-context model over the recording for summary and action items; speaker diarization from ASR; retrieval over past meetings; privacy controls (consent, retention, PII redaction) dominate the design.

**Interview line:** *"I decide by token economics and auditability: multimodal LLMs for open-ended reasoning over mixed inputs, specialized vision or audio models for high-volume fixed tasks, and a hybrid with a layout model plus LLM where regulators want bounding boxes and confidences. Every multimodal path gets its own eval set, because text evals never catch a broken vision pipeline."*
