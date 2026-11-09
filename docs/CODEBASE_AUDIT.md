# TrimCircle codebase audit

Audit date: 2026-11-09. Baseline: commit `f9f9e18`. The baseline suite had 12 passing tests. Passing tests demonstrate software behavior only; there is no labelled face-shape or hairstyle-suitability dataset in the repository, so real-world accuracy is unknown.

## Current architecture

FastAPI serves the static studio and upload/JSON APIs. Pillow performs basic decoding and quality checks. MediaPipe Face Landmarker runs server-side for analysis and overlay anchors. Recommendations use deterministic rules over a JSON catalog. Optional try-on jobs use SQLite and temporary files under `runtime/jobs`; a polling worker can call a configured GPU HTTP provider.

## Findings

| Severity | Finding | Evidence | Decision |
|---|---|---|---|
| Critical | Try-on status, package, result upload/download, and deletion are authorized only by possession of a UUID. Worker result upload has no worker credential. | `app/job_api.py` | Rebuild job authorization before public deployment. |
| High | Face distances used normalized x/y space, distorting geometry for non-square images. | former `_distance` in `app/face_analysis.py` | Replaced with original-image pixel geometry. |
| High | Face-shape percentages were fixed constants and presented as confidence. | former `_classify`; `app/static/studio.js` | Removed; return an alternative and uncertainty. |
| High | Classification used only front landmarks. Side views affected pose messages but not classification. | `analyze_views` | Add valid view-specific profile evidence without treating it as frontal width. |
| High | Pose classification is an uncalibrated nose-position heuristic; either profile previously passed either side. | `analyze_views` | Strict view matching fixed; calibrated head pose remains incomplete. |
| High | No labelled evaluation set, person-disjoint split, confusion matrix, calibration analysis, or human recommendation ratings exist. | repository-wide | Build evaluation tooling and make no accuracy claim. |
| Medium | EXIF orientation was inconsistent across validation and analysis. | `app/image_validation.py`, former `app/face_analysis.py` | Standardized with `ImageOps.exif_transpose`. |
| Medium | Validation lacks multiple-face, landmark-occlusion, and calibrated-pose checks. | validation and landmarker options | Exposure checks added; remaining checks are incomplete. |
| Medium | Recommendation weights and compatibility labels are manually authored and unvalidated. | `app/recommender.py`, catalog | Keep as transparent baseline; require human evaluation. |
| Medium | Hair density lacks `unknown`; hair attributes are user supplied. | `app/models.py` | Add a compatible schema revision and confirmation flow. |
| Medium | CPU-bound MediaPipe inference runs inside an async handler and creates a landmarker per request. | `app/main.py`, `app/face_analysis.py` | Move inference off the event loop and bound concurrency. |
| Medium | GPU result bytes are stored without local decode, size, or dimension validation. | `app/provider.py` | Validate provider output before storage. |
| Low | Externalized catalog, deterministic filters, provider abstraction, UUID job directories, expiry cleanup, and upload limits are reusable. | relevant modules | Preserve and harden. |

## Reuse versus rebuild

- Reuse with tests: FastAPI shell, catalog loading, deterministic filtering, provider abstraction, UUID job directories, expiry cleanup, and 2D overlay separation.
- Improve in place: image validation, frontend guidance, recommendation metadata/explanations, worker output validation, and resource bounds.
- Replace behind stable APIs: facial geometry/classification internals and try-on authorization.
- Do not add a learned model until a legally usable, independently labelled dataset passes license, diversity, leakage, and annotation review.

## Current limitations

Category thresholds remain hypotheses, not validated decision boundaries. MediaPipe landmarks are styling proxies, not exact anatomical forehead or cheekbone boundaries. Side-view metrics are now reported but do not change the label because no paired three-view calibration data is available.
