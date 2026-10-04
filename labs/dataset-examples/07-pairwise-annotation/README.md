# 07: Pairwise annotation without ground truth

## What this dataset is for

"Which video better answers *how to make pour over coffee for beginners*?" has no answer key. The label is a measurement of human judgment, like a panel of competition judges: record each judge, measure how much they agree, and treat disagreement as information about the item rather than noise to be averaged away. Such data trains and evaluates search, recommendation and reward models, and its quality must be established without anything to compare it with: by agreement statistics, hidden gold items and bias checks.

The question this folder answers is: *when nobody knows the right answer, how do you know the labels are any good?*

## The example

`raw_annotations.csv` holds 45 judgments: 8 video-relevance pairs (`P-01` to `P-08`) and one gold item (`G-01`), each judged by 5 annotators. Two rows of `P-01` and one of the gold item:

```csv
item_id,query,video_a,video_b,shown_left,annotator_id,choice,confidence,seconds_spent,reason_tags,is_gold,gold_answer
P-01,how to make pour over coffee for beginners,vid_8812 | Pour-over coffee in 3 minutes (beginner guide),vid_2290 | World barista championship final routine,A,ann_201,A,5,21,beginner_level;answers_query,false,
P-01,how to make pour over coffee for beginners,vid_8812 | Pour-over coffee in 3 minutes (beginner guide),vid_2290 | World barista championship final routine,B,ann_204,B,2,52,production_quality,false,
G-01,replace bike inner tube,vid_9031 | Top 10 sports cars of 2026,vid_1458 | Replace a bike inner tube step by step,B,ann_206,A,4,6,production_quality,true,B
```

| Field | What it is and why it exists |
|---|---|
| `item_id` | groups an item's five judgments; `G-` marks gold |
| `query`, `video_a`, `video_b` | the item, identical across its rows |
| `shown_left` | which video this annotator saw on the left; randomised, which makes position bias measurable |
| `annotator_id` | per-annotator statistics and screening |
| `choice` | `A`, `B` or `tie`, naming a video, not a side |
| `confidence`, `seconds_spent` | certainty and effort; low values predict disagreement or carelessness |
| `reason_tags` | why, in a fixed vocabulary that feeds guideline revisions |
| `is_gold`, `gold_answer` | hidden checks with a known answer |

## How the model uses it

**Aggregate.** Each item gets a majority where one exists and a soft label always. `annotation_demo()` in `how_models_use_it.py` computes both, then the agreement statistics and the gold result; run `python3 how_models_use_it.py` from the lab root:

```text
[ANNOT] P-01: votes {'A': 4, 'B': 1} majority A (4/5); soft label {'A': 0.8, 'B': 0.2, 'tie': 0.0}
[ANNOT] P-04: votes {'A': 2, 'B': 2, 'tie': 1} no majority: adjudicate or keep only the soft label; soft label {'A': 0.4, 'B': 0.4, 'tie': 0.2}
[ANNOT] P-08: votes {'B': 3, 'A': 2} majority B (3/5); soft label {'A': 0.4, 'B': 0.6, 'tie': 0.0}
[ANNOT] Fleiss' kappa 0.351; Krippendorff's alpha (nominal) 0.367
[ANNOT] gold item: 4/5 correct; failed: ['ann_206']
```

(The script prints all eight items; three are shown.) **Measure agreement.** `fleiss_kappa(table)` compares observed with chance agreement: observed is the share of agreeing annotator pairs per item (1.0 on unanimous items, 0.2 on P-04), averaging 0.6375; chance from the label shares (21 A, 16 B, 3 ties of 40) is 0.525² + 0.40² + 0.075² = 0.441; κ = (0.6375 − 0.441) / (1 − 0.441) = 0.351. `krippendorff_alpha_nominal(units)`, with a small-sample correction and support for missing raters, gives 0.367. That is "fair" on the conventional bands, and typical of subjective relevance; the response is to keep soft labels, revise guidelines where items split, and find where the disagreement lives.

**Check gold.** For "replace bike inner tube", `ann_206` picked *Top 10 sports cars of 2026* in 6 seconds, the fastest time on the item, citing `production_quality`; the miss goes on that annotator's record.

**Find position bias.** Because sides are randomised, count how often the chosen video was on the left: 26 of 37 non-tie choices. On the unanimous items (P-03, P-06, P-07) the left video won 8 of 15 times, as randomisation predicts. On the two closest items, P-04 (2–2–1) and P-08 (3–2), every non-tie choice went left, 9 of 9: P-08's majority is the randomisation speaking. Treat such items as uncertain and give them more judgments with sides balanced.

**Train on soft targets.** A pairwise ranker models P(A beats B) = σ(s_A − s_B) and minimises cross-entropy against the soft target (counting a tie as half a vote each way: 0.8 for P-01, 0.5 for P-04, 0.4 for P-08). A hard label would reward confidence the humans lacked. **Evaluate retrieval** by how often a system ranks the human-preferred video higher, against the annotators' own agreement as the ceiling.

## How it is produced and checked

Guidelines define relevance, ties and the boundary cases that split annotators ("beginner" against "complete"); five judgments per item with randomised sides; unannounced gold items at a fixed rate; time, confidence and reason tags recorded; extra judgments or adjudication for close items; calibration sessions on disagreements.

`validate_all.py` check **07 pairwise annotation (no ground truth)** asserts: `choice` in {A, B, tie} and `shown_left` in {A, B}; confidence 1 to 5 and positive seconds; identical query and video text across an item's rows; exactly five distinct annotators per item; valid gold answers on gold rows; and κ and α recomputed through `how_models_use_it.py` and pinned at exactly 0.351 and 0.367, so any edit to the file that changes them fails. It prints `45 judgments, 5 per item; Fleiss' kappa 0.351, Krippendorff's alpha 0.367`.

## What goes wrong

- **Forcing majorities** on close items or dropping ties throws away the uncertainty a model needs; **reading κ as accuracy**.
- **No side randomisation** hides position bias and bakes it into labels; here it would have made P-08 look settled.
- **Gold too easy** catches only spammers, **gold too ambiguous** punishes careful annotators; and removal rules must be fixed before anyone sees their effect on κ (dropping the tie-heavy `ann_204`, who never saw the gold item, would lift α to 0.557).

## Related

Chapter 26d.8 (the full position-bias table, per-annotator telemetry, RankNet and soft-label entropy). Siblings: `02-preference/` and `04-rlaif/` (pairwise judgment where a right answer exists), `15-golden-and-qa/` (gold accuracy per annotator and lot acceptance), `16-ops-telemetry/` (where seconds and rework become cost).
