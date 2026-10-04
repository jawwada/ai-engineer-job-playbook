# 09: Egocentric video for robotics

## What this dataset is for

A robot that will work in kitchens benefits from watching thousands of hours of people doing kitchen tasks through their own eyes: what hands do, which objects they touch, in what order. Annotations turn raw first-person video into "this action, from here to here, with this hand and this object", plus a sentence describing it. Those labels train perception models (action recognition, anticipation, video–language alignment, hand–object detection) whose representations give robot policies a head start. The question this folder answers is: *how does a 24-second clip of someone making coffee become training examples, and what has to be true of the labels and the consent behind them?*

## The example

Two files. `clip_manifest.json` describes the recording and its legal basis; `clip_annotations.json` holds the labels. The manifest, trimmed:

```json
{"clip_id": "ego-kit-000731-c03", "session_id": "ego-kit-000731",
 "device": {"type": "head-mounted camera", "model": "generic-egocam-v2"},
 "fps": 30, "resolution": [1920, 1080], "duration_s": 24.0, "frames": 720,
 "scene": "home kitchen", "task": "finish a pour-over coffee",
 "consent_id": "cons-55190", "contributor_id": "contrib-0882",
 "privacy": {"faces_blurred": true, "screens_blurred": true, "audio_removed": true, "location_removed": true},
 "protocol_version": "ego-collect-v4.2",
 "storage_uri": "s3://example-bucket/ego/2026-08/ego-kit-000731-c03.mp4"}
```

The annotations, trimmed to one element of each kind:

```json
{"clip_id": "ego-kit-000731-c03", "annotation_version": "ego-annot-v3.0",
 "taxonomy": {"verbs": "verb-list-v3 (take, put-down, pour, lift, place, stir, ...)", "nouns": "noun-list-v3"},
 "narrations": [{"t_s": 0.8, "text": "#C C takes the kettle with the right hand"}, "... 6 more"],
 "actions": [{"id": "a1", "start_s": 0.6, "end_s": 2.4, "verb": "take", "noun": "kettle", "hands": "right"},
             {"id": "a2", "start_s": 2.4, "end_s": 9.6, "verb": "pour", "noun": "water", "target": "dripper", "hands": "right"}, "... 5 more"],
 "object_tracks": [{"track_id": "kettle-1", "category": "kettle",
                    "boxes": [{"frame": 18, "bbox_xywh": [1210, 610, 260, 300]}, {"frame": 72, "bbox_xywh": [1030, 420, 280, 320]}, "..."]}, "..."],
 "hand_object_contact": [{"start_s": 0.6, "end_s": 11.0, "hand": "right", "track_id": "kettle-1"}, "..."],
 "qc": {"second_pass_temporal_iou": 0.81, "boxes_audited_fraction": 0.1, "privacy_check": "passed",
        "annotator": "ann_v12", "reviewer": "rev_v03", "prelabel_model": "vlm-prelabeler-2026-07", "human_minutes": 9.5}}
```

| Field | What it is and why it exists |
|---|---|
| `clip_id`, `session_id` | joins annotations to video; a session's clips stay in one split |
| `fps`, `resolution`, `duration_s`, `frames` | converting seconds to frames and boxes to pixels |
| `consent_id`, `contributor_id` | the legal basis for use, and the link for withdrawal requests |
| `privacy` | de-identification done before annotation |
| `protocol_version`, `annotation_version`, `taxonomy` | labels compare only within one protocol and taxonomy version |
| `narrations[]` | timestamped sentences in Ego4D's convention: `#C` marks an action by the camera wearer, called C in the text |
| `actions[]` | segments with `verb`, `noun`, optional `target` or `tool`, and `hands` |
| `object_tracks[]` | boxes `[x, y, width, height]` at keyframes |
| `hand_object_contact[]` | which hand touches which tracked object, when |
| `qc` | second-pass temporal IoU, share of boxes audited, privacy check, pre-labeling model, human minutes |

## How the model uses it

`video_demo()` in `how_models_use_it.py` converts the action segments to frame ranges at 30 fps and sums their coverage; run `python3 how_models_use_it.py` from the lab root:

```text
[VIDEO] 7 action segments cover 22.7 of 24.0 s; first training clip 'take kettle' = frames 18-72; verbs {'take': 2, 'pour': 1, 'put-down': 1, 'lift': 1, 'place': 1, 'stir': 1}
```

**Action recognition.** Each segment becomes a training clip ("take kettle" is frames 18–72, "pour water" 72–288) from which a model samples a fixed number of frames and predicts verb and noun. **Anticipation.** The model sees video only up to a fixed time before an action and predicts it; with a 1-second horizon, "lift dripper" at 11.2 s is predicted from video ending at 10.2 s (frame 306), while the kettle is still being put down. **Video–language pretraining.** Each narration with a clip around its timestamp is a (video, text) pair for contrastive learning with an InfoNCE-style loss. **Detection and interaction.** Keyframe boxes (the kettle at frames 18, 72, 180, 288) train detectors and trackers; contact intervals train hand–object models. **Robot learning.** A visual encoder pretrained on such video is frozen as a robot's perception module, or human video with hand tracking is co-trained with robot demonstrations; joint commands still come from robot data. The 1.3 s of gaps between segments are transitions that a model needs as a background class or must ignore deliberately.

## How it is produced and checked

A protocol (`ego-collect-v4.2`) defines devices, scenes, tasks and consent; de-identification runs before annotators see anything; a vision–language model pre-labels (`vlm-prelabeler-2026-07`); annotators correct segments, narrations, boxes and contacts (9.5 minutes for this clip); a second pass measures temporal agreement (IoU 0.81); 10% of boxes are audited; the taxonomy is versioned.

`validate_all.py` check **09 egocentric video annotations** asserts: the annotation and manifest clip ids match; `frames` equals fps × duration; every privacy flag is true and a consent id is present; actions do not overlap and lie inside the clip; every narration starts with `#C C ` and falls inside an action; every box's frame is in range and the box lies inside 1920 × 1080; every contact names a real track. It prints `7 non-overlapping actions; every narration inside an action; boxes inside 1920x1080`. Acceptance adds a minimum temporal IoU between passes and a box-audit error rate.

## What goes wrong

- **Boundaries are judgments**: measure agreement between passes instead of assuming it; **free text against fixed classes** ("picks up the mug" narrates the verb class `take`), so version the mapping.
- **Splits by clip** leak near-identical footage; split by session or contributor.
- **Privacy leaks** through reflections or screens, consent withdrawals that must reach every derived file, and frame drift after re-encoding.

## Related

Chapter 26d.10 (EPIC-KITCHENS-100, Ego4D narrations, EgoVLP, 100DOH, R3M, VIP, EgoMimic). Siblings: `13-delivery/` (manifests and consent travel with the data), `15-golden-and-qa/` (audit fractions and second-pass agreement as acceptance evidence), `07-pairwise-annotation/` (agreement statistics for labels without ground truth).
