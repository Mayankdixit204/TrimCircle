AI HAIRCUT  
RECOMMENDATION ENGINE

Complete Technical Specification

Architecture • Dataset plan • Evaluation • Privacy • Roadmap

| PROJECT SNAPSHOT | CURRENT DECISION |  |
| --- | --- |
| Status | Planning only — implementation has not started. |  |
| Input | Three still photos: front, left-side and right-side. |  |
| Scope | Standalone recommendation engine; no website integration or virtual try-on in the first version. |  |
| Initial cost goal | ₹0 in paid AI API fees. Hosting, storage, data collection and licensing may still cost money. |  |
| Primary stack | Python + FastAPI; browser-side JavaScript/TypeScript + MediaPipe where practical. |  |
| Recommendation plan | Rules-based baseline first; train a learned ranker only if labelled data and evaluation justify it. |  |

Version 2.1  •  21 October 2026

This document defines a plan. It does not claim that code, a trained model, dataset permissions or target accuracy have already been validated.

# Document guide

Use this document as the single planning reference. Items marked as proposed targets are engineering goals to validate, not established performance claims.

| Section | Contents |  |
| --- | --- |
| 1–3 | Summary, objectives, scope and technology choices |  |
| 4–6 | System flow, three-view processing, face-shape estimation and hairstyle ranking |  |
| 7–8 | Dataset research, labels, data collection and API contract |  |
| 9–11 | Data storage, evaluation gates, cost boundaries and deployment |  |
| 12–14 | Privacy, security, testing, monitoring and repository structure |  |
| 15–18 | Roadmap, unresolved decisions, risks and final decisions |  |

# Document status and revision notes

Version 2.1 reorganizes the prior specification into a cleaner technical document, standardizes headings and tables, and adds missing implementation controls.

Added/clarified: API error behavior, image-quality failure handling, data/licence register, split strategy, reproducibility, deployment and monitoring, security testing, acceptance criteria, and decisions still requiring validation.

External dataset descriptions are leads for investigation, not a legal approval or guarantee of commercial-use rights.

The system remains in planning; no implementation or measured accuracy is claimed.

# 1. Executive summary

The planned AI Haircut Recommendation Engine will use three labelled still photos—front, left side and right side—to estimate facial geometry and support hairstyle recommendations. Recommendations will also consider hair texture, density and length (with uncertainty where these cannot be inferred reliably), maintenance needs, styling effort and user preferences.

The project has two separate quality goals: (1) face-shape estimation and (2) ranking hairstyles that a person may find suitable. Success on the first task does not prove success on the second. A rules-based baseline will be implemented first; a learned ranking model is a later option only if useful, consented, consistently labelled data becomes available.

Core operating principle: validate every view, preserve uncertainty, explain limitations, and ask for a retake or user correction rather than inventing measurements or forcing a confident result.

# 2. Objectives and scope

## 2.1 Objectives

Accept three labelled photos: front, left-side and right-side.

Validate file properties, view labels, face visibility, sharpness, pose and consistency.

Estimate face shape from appropriate facial features and report uncertainty.

Support men's, women's and unisex hairstyle catalog entries without using gender as a rigid eligibility rule.

Rank styles using facial proportions, hair characteristics, maintenance, styling effort and explicit preferences.

Explain why each style was recommended and identify the catalog reference assets.

Keep paid AI API fees at ₹0 initially, using open-source/local processing where practical.

Measure face-shape and hairstyle-ranking performance separately before making accuracy claims.

Minimize collection and retention of original photos and personal data.

## 2.2 Out of scope for the first version

Website/mobile UI implementation and integration into another product.

Virtual try-on, face swapping, generated hairstyle previews or live-video tracking.

Paid hosted AI inference APIs.

Public endpoints for model training.

Face recognition, identity matching or facial identity embeddings.

Claims of professional-level accuracy before independent evaluation.

# 3. Recommended technology stack

| Layer | Choice | Reason / caveat |  |
| --- | --- | --- |
| Backend language | Python | Convenient ecosystem for ML, feature engineering, APIs and evaluation. |  |
| API | FastAPI + Pydantic | Typed request/response validation and automatic API documentation. |  |
| Browser analysis (planned) | JavaScript/TypeScript + MediaPipe | Run landmarks locally where practical to avoid uploading original selfies by default. Confirm the chosen MediaPipe package/model licence and browser support before implementation. |  |
| Numerical work | NumPy; pandas | Feature calculations and dataset processing. |  |
| Baseline ML | Rules + scikit-learn | Simple, inspectable baseline and standard evaluation metrics. |  |
| Candidate learned ranker | CatBoost ranking or another suitable ranker | Choose only after label format and dataset size are known; benchmark against baseline. |  |
| Storage | SQLite locally; PostgreSQL if justified | Start simple. Do not add production infrastructure before it is needed. |  |
| Testing | pytest + HTTPX | Unit, API contract, ranking, failure-path and privacy tests. |  |
| Packaging | Docker, optional initially | Reproducible deployment; not required to begin local experiments. |  |

Why not start with Java/Spring Boot? It is capable, but Python keeps the initial ML and API stack simpler. A separate Java backend is unnecessary for the first standalone prototype.

# 4. System architecture and processing flow

## 4.1 Processing flow

The user captures or selects three photos and explicitly labels each view.

The client validates basic file properties and checks that the requested views are present.

Where practical, browser-side landmark detection runs locally; original images are not sent to the server by default.

Each view receives its own quality result and feature set. Unsupported measurements remain missing, not guessed.

A multi-view fusion step combines only compatible, reliable evidence and records conflicts or missing views.

The face-shape estimator returns a category with uncertainty, or returns uncertain/retake.

The catalog filter removes styles that conflict with hard constraints such as desired length or excluded styles.

The ranking component orders remaining styles and generates grounded reasons from catalog attributes.

The API returns ranked styles, warnings, model version and fallback status.

Optional consent-based feedback is stored for evaluation; training remains an offline workflow.

## 4.2 Capture guidance

Use a neutral expression, even lighting and a camera approximately at face level.

Keep the whole face visible; avoid beauty filters, strong shadows and heavy occlusion.

Front photo: face directed toward the camera. Side photos: capture true left and right profiles consistently.

Avoid extreme wide-angle perspective and very close camera distance.

Keep hair visible where possible, but do not require the forehead to be uncovered if the user cannot or does not wish to do so.

Do not assume the three photos belong to the same person solely because the client labels them together; the initial system should flag obvious inconsistencies where feasible.

## 4.3 Three-view evidence map

| View | Potential evidence | Important limitations |  |
| --- | --- | --- |
| Front | Frontal proportions; forehead/cheek width; visible hairline and overall facial outline. | Perspective, expression, bangs/hair covering forehead and camera distance can distort measurements. |  |
| Left side | Side profile; visible jaw/chin contour; temple and side-hair appearance. | Cannot provide all frontal widths; head rotation and lens perspective can distort profile. |  |
| Right side | Second profile; visible side-hair appearance; consistency check. | Natural asymmetry is normal. Disagreement should trigger review/uncertainty, not forced averaging. |  |

## 4.4 Multi-view fusion rules

Track each feature's source view, quality, validity and any transformation applied.

Use only measurements that are geometrically meaningful for that view; do not infer a frontal width from a side photo without a validated method.

Normalize ratios where appropriate to reduce sensitivity to image size; document the formula and expected range for each feature.

Do not average incompatible measurements blindly. Preserve per-view values and define explicit conflict handling.

If a critical view is missing, poor quality or contradictory, return a partial/uncertain result or request a retake according to a documented policy.

# 5. Face-shape estimation

## 5.1 Candidate features

Potential features include face length-to-width ratio, forehead-to-cheekbone width, jaw-to-cheekbone width, jaw/chin contour, cheekbone prominence and profile cues. Final features must be selected only after testing whether the chosen landmark model measures them reliably in the intended views.

Not every candidate feature is visible or valid in every view. Define a feature dictionary with its formula, required landmarks, source view, units/range, missing-value behavior and known failure cases.

## 5.2 Initial categories

Oval, round, square, oblong, heart, diamond, and mixed/uncertain. These are simplified styling conventions, not universally objective medical or anatomical classes. The annotation guide must define each label and explicitly permit disagreement or mixed cases.

## 5.3 Method

Begin with an interpretable geometry/rule baseline rather than assuming a large image classifier is necessary.

Create a written annotation guide and label examples consistently.

Have at least two reviewers independently label a subset; record agreement and disagreement.

Compare any trained classifier against the baseline using participant-level held-out data.

Allow an uncertain outcome when views disagree, quality is poor or evidence is near a class boundary.

Do not display probability percentages unless the model has been calibrated and the percentages have a defined interpretation.

# 6. Hairstyle catalog and recommendation engine

## 6.1 Catalog schema

| Attribute | Examples / rule |  |
| --- | --- |
| Identity | Stable hairstyle ID, display name, description and catalog version. |  |
| Style family | Fade, buzz cut, bob, layers, pixie, fringe, curls, braids and other documented styles. |  |
| Length | Short, medium, long; define categories consistently. |  |
| Texture compatibility | Straight, wavy, curly, coily, mixed or unknown. |  |
| Density / hairline | Fine, medium, thick; hairline notes where useful. Allow unknown and avoid overconfident visual inference. |  |
| Face compatibility | Reviewer-assessed compatibility and reasons; not a universal truth. |  |
| Maintenance / effort | Low, medium or high, with a clear definition for each level. |  |
| Preferences | Desired look, disliked styles, length constraints, styling time and other user-selected priorities. |  |
| Tags | Men's, women's, unisex or other useful tags; optional filters, not rigid eligibility rules. |  |
| Assets / rights | Image URL or asset ID, source, creator if known, licence, allowed uses, attribution and verification date. |  |

## 6.2 Three-stage recommendation plan

### Stage 1 — Rules-based baseline

Filter styles using hard user constraints first. Rank the remaining candidates with documented, inspectable rules based on face proportions, hair characteristics, maintenance, styling effort and preferences. Return concise reasons tied to actual catalog attributes. This is a baseline, not a claim of learned intelligence.

### Stage 2 — Human-labelled comparisons

With appropriate consent, ask qualified stylists and/or users to rate suitability or compare pairs of styles. Capture the context and reasons, reviewer role, confidence, date and annotation-guide version. Avoid collecting identity data that is not necessary.

### Stage 3 — Learned ranking model

Only after enough relevant labels exist, train a ranking model offline. Compare it with the rules baseline on participants and styles excluded from training. Keep a model registry with dataset version, feature schema, code version, metrics and release decision. Do not release a learned model unless the improvement is repeatable and does not introduce unexplained subgroup failures.

## 6.3 Ranking score and explanations

A ranking score is an ordering signal, not a probability of suitability.

Reasons must be traceable to known inputs or catalog metadata; do not invent claims about hair texture, density or face shape.

If hair attributes are unknown, either ask the user or reduce the weight of those features.

Support user corrections, preference changes and 'not interested' feedback.

Keep a deterministic fallback available if a trained model or dependency is unavailable.

# 7. Dataset research and acquisition

Public resources can support individual subtasks. A face-shape dataset may help explore face-shape labels; a hair segmentation dataset may help locate hair pixels. Neither task alone teaches the system which haircut is suitable for a particular person.

## 7.1 Candidate resources to investigate

| Resource | Potential use / reported contents | Verification required | Link |  |
| --- | --- | --- | --- |
| Niten Lama Face Shape Dataset (Kaggle) | Reported five labels: heart, oblong, oval, round and square; approximately 5,000 images have been reported by secondary project references. | Inspect the current dataset page, class balance, source images, label process, duplicates, population coverage and licence. Do not assume three views per person or commercial rights. | https://www.kaggle.com/datasets/niten19/face-shape-dataset |  |
| Figaro-1k / HairAnalysis | Project README describes 1,050 images across seven hair-related categories with manually segmented hair masks. | Useful for hair segmentation/appearance exploration, not haircut suitability. Check data and code/model licences separately before reuse. | https://github.com/UmarSpa/HairAnalysis |  |
| DSMLR face-shape repository | Potential additional face-shape resource. | Inspect actual data availability, labels, source, licence and whether identities/views can be linked; do not assume multi-view records. | https://github.com/dsmlr/faceshape |  |
| Face-shape prediction implementation | Can be reviewed for preprocessing and baseline ideas. | Code licence, pretrained-weight licence and training-data rights are separate; inspect each before reuse. | https://github.com/Diksha-cmd/face-shape-prediction |  |

Verification note: repository pages and third-party summaries are discovery aids, not legal clearance. Record the exact licence/terms, source and date checked for each dataset, model weight and reference image before using it in a public or commercial product. The HairAnalysis repository README confirms the reported Figaro-1k image count and task description. See https://github.com/UmarSpa/HairAnalysis and its associated paper at https://doi.org/10.1016/j.imavis.2018.02.001.

## 7.2 Critical dataset gap

No single ready-made dataset has been verified for this plan as containing all of the following together: front, left and right photos of the same person; consistent face-shape labels; hair texture/density/hairline attributes; a structured hairstyle catalog; and expert/user judgments of haircut suitability. Plan for separate datasets and a consent-based collection effort.

## 7.3 Data plan

Create a dataset register with source, licence, permitted use, attribution, collection date, restrictions and decision owner.

Keep face-shape labels, hair-segmentation labels and haircut-suitability labels as separate tasks.

Collect three-view records only with suitable consent and clear notice of intended use, retention and deletion.

Collect multiple independent ratings or pairwise comparisons for recommendations; store reviewer disagreement rather than hiding it.

Version raw/processed data, annotation guidance, feature code and exclusions.

Split all data by participant before training/validation/test so one person's views or near-duplicates cannot leak across splits.

Check near-duplicate images, class imbalance, demographic coverage and data-quality failures before training.

## 7.4 Minimum data record design

| Record | Fields to consider |  |
| --- | --- |
| Participant / consent | Random pseudonymous participant ID, consent version/status, permitted purposes, withdrawal/deletion status; keep identity/contact details separate if they are needed at all. |  |
| Photo/view | Participant ID, view label, capture guidance version, quality flags, source/licence or consent basis, retention/deletion status. |  |
| Features | Feature schema version, value or missing status, source view, quality/confidence flag, calculation version. |  |
| Face-shape annotation | Label, reviewer ID/role in pseudonymous form, guide version, timestamp, confidence and disagreement status. |  |
| Style asset | Style ID, asset ID, source, licence/permission, attribution, allowed use and verification date. |  |
| Suitability judgment | Participant/profile context needed for rating, candidate style IDs, rating or pairwise preference, reason tags, reviewer role, confidence and guide version. |  |

# 8. API contract

## 8.1 POST /v1/recommendations

Purpose: accept validated measurements and preferences and return ranked hairstyle candidates. For the initial privacy-preserving design, original photos are analysed on the client where practical; the backend receives structured features rather than selfies. If server-side image uploads are introduced later, treat that as a separate privacy/security decision.

Request schema must define required and optional fields, units, allowed ranges, missing-value behavior, versioning and validation errors. The following is illustrative only; values are examples, not validated thresholds:

{  
  "schema_version": "2.1",  
  "views": {  
    "front": {"quality": "acceptable", "features": {"face_length_to_width": 1.42}},  
    "left":  {"quality": "acceptable", "features": {"profile_quality": "acceptable"}},  
    "right": {"quality": "acceptable", "features": {"profile_quality": "acceptable"}}  
  },  
  "hair_profile": {"texture": "unknown", "density": "unknown", "length": "medium"},  
  "preferences": {"maintenance": "low", "excluded_styles": []}  
}

## 8.2 Response requirements

Request ID, API/schema version and model/ruleset version.

Face-shape estimate plus uncertainty/quality status, or explicit uncertain result.

Per-view quality status and actionable retake warnings.

Ranked hairstyle IDs, ranking scores, and explanations tied to catalog fields.

Catalog asset identifiers and any known image usage restrictions.

Model status: rules fallback or trained model; do not imply a learned model exists before it does.

Explicit partial-input or fallback indication.

## 8.3 Additional endpoints

| Endpoint | Purpose / rules |  |
| --- | --- |
| GET /v1/hairstyles | Filter and paginate public catalog entries; do not expose private training records. |  |
| POST /v1/feedback | Optional ratings/pairwise comparisons linked to a request and style; consent and data-minimization controls apply. |  |
| GET /health/live | Confirms the process is alive. |  |
| GET /health/ready | Confirms required configuration and model/catalog artifacts are ready. |  |

## 8.4 Error handling

Use consistent error codes for missing views, unsupported formats, invalid values, quality rejection, rate limiting and internal failures.

Return safe, actionable messages without exposing stack traces, secrets or stored personal data.

Set documented request-size limits and timeouts; validate both client inputs and backend schemas.

Training and evaluation are offline commands, not public endpoints.

# 9. Storage and model management

| Table / area | Purpose |  |
| --- | --- |
| hairstyles / hairstyle_attributes | Catalog entries and structured compatibility metadata. |  |
| reference_assets | Asset source, rights, attribution, allowed use and verification date. |  |
| stylist_judgments | Expert labels and pairwise comparisons; pseudonymous reviewer references. |  |
| recommendation_feedback | Optional user feedback with purpose/retention controls. |  |
| model_versions / training_runs | Artifact versions, dataset/feature versions, code revision, metrics and release status. |  |
| dataset_sources / consent_records | Dataset provenance, licence/consent basis, restrictions and deletion/withdrawal tracking. |  |

Do not retain original photos or measurements by default without a clear need. If research data is retained, separate participant identity/contact details from analytical records, restrict access and document retention/deletion. SQLite is sufficient for local development; move to PostgreSQL only when the deployment or concurrency needs justify it.

# 10. Accuracy evaluation and release gates

## 10.1 Face-shape evaluation

A first study might aim for 300–500 consenting participants with varied face shapes, hair types, ages, skin tones and capture conditions. This is a planning range, not a statistical-power guarantee. Determine final sample size based on class balance, expected uncertainty and the improvement to be detected.

Macro F1, precision and recall for each class, and confusion matrix.

Independent-reviewer agreement and frequency of ambiguous/mixed labels.

Uncertain/rejected prediction rate and retake rate.

Calibration analysis before displaying probability percentages.

Performance by view quality, relevant user groups and capture conditions.

Failure review for incorrect landmarks, occlusion, perspective and conflicting views.

## 10.2 Haircut suitability evaluation

A preliminary study might use 100–200 participants with multiple independent ratings per participant. The appropriate sample size depends on rating variability and the effect the team wants to detect.

Top-5 relevance: proportion of the top five suggestions rated suitable under the agreed rubric.

NDCG@5 or another ranking metric to assess whether stronger-rated styles appear higher.

Preference agreement on held-out comparisons.

Catalog coverage and performance for different hair characteristics and preferences.

Improvement over the rules baseline, including uncertainty and failure cases.

Reviewer agreement; distinguish stylist judgment from individual user preference.

## 10.3 Proposed initial release gates

| Area | Proposed gate | Interpretation |  |
| --- | --- | --- |
| Face-shape classification | Macro F1 ≥ 0.80 on participant-level held-out data, with per-class review. | An internal target, not an industry benchmark or guaranteed result. |  |
| Probability display | Calibration evaluated and documented. | If not calibrated, show a category/uncertainty status rather than a probability. |  |
| Haircut ranking | NDCG@5 or agreed metric improves over the baseline on independent data. | A learned model must demonstrate measurable improvement. |  |
| Data leakage | No participant or near-duplicate leakage across splits. | Required for credible evaluation. |  |
| Quality failures | Poor/contradictory inputs trigger retake or uncertain result. | Do not force a confident answer. |  |
| Privacy/security | Threat and retention review completed; automated checks pass. | No release while critical issues remain unresolved. |  |
| Operations | Latency, error rate and fallback behavior measured. | Set concrete limits after local benchmarks and deployment target are known. |  |

If a target is missed, improve the data, definitions or method and report the result honestly. Do not change the metric or test set just to make a result pass.

# 11. ₹0 paid AI API strategy and cost boundaries

| Component | Initial approach | Expected paid AI API fee |  |
| --- | --- | --- |
| Facial landmarks | Open-source/local browser inference where practical | ₹0 API fee |  |
| Facial geometry | Python calculations | ₹0 API fee |  |
| Baseline classifier | Rules and scikit-learn | ₹0 API fee |  |
| Learned ranker | Locally trained CatBoost/scikit-learn model | ₹0 API fee |  |
| Backend | FastAPI locally | ₹0 software/API fee |  |
| Database | SQLite locally | ₹0 software/API fee |  |
| Testing/evaluation | pytest, HTTPX and local Python | ₹0 API fee |  |

₹0 in paid AI API fees does not mean ₹0 total cost. Hosting, domain, storage, bandwidth, backups, production database, image licensing, annotation and time spent collecting/reviewing data may cost money. Free hosting plans can impose sleep, quota, performance, storage or reliability limits. Verify current provider terms before deployment.

# 12. Privacy, security and responsible use

Prefer local photo processing and send only the measurements/preferences needed by the API.

Do not create face-recognition features or identity embeddings.

Explain the purpose of any retained data and obtain appropriate consent for collection and training.

Provide a documented deletion/withdrawal process for retained personal data where applicable.

Validate input schemas, ranges, file types, request sizes, timeouts and rate limits.

Use HTTPS, secure secrets management, least-privilege access and protected model artifacts in production.

Do not log original photos, raw feature payloads, access tokens or unnecessary personal information.

Keep consent/contact data separate from analytical records; pseudonymous IDs are not the same as anonymous data.

Track dataset/model/image rights separately and do not use an image commercially unless the relevant rights permit the intended use.

Test for uneven failure rates and suitability quality across relevant groups; document limitations and avoid presenting styling categories as objective truths.

A backend cannot independently prove that submitted measurements genuinely came from the intended photos. Client-side analysis improves privacy but is not a security guarantee. If trust or abuse prevention becomes important, define a proportionate validation approach without collecting more sensitive data than necessary.

# 13. Testing, reproducibility and operations

## 13.1 Test plan

Unit tests for feature formulas, valid ranges, missing features and view-specific constraints.

API contract tests for valid requests, malformed payloads, missing views and unsupported schema versions.

Failure-path tests for no face detected, multiple faces, poor lighting, occlusion, rotated views and conflicting profiles.

Ranking tests that verify hard constraints, deterministic fallback and explanations matching catalog metadata.

Privacy tests that ensure image/personal payloads are not written to logs or retained unexpectedly.

Data tests for duplicate participants, split leakage, missing labels, class imbalance and licence metadata.

Regression tests on a fixed, permissioned evaluation set whenever feature code or model versions change.

## 13.2 Reproducibility and monitoring

Version the feature schema, annotation guide, dataset snapshot, training code, model artifact and catalog.

Record environment/dependency versions and random seeds where relevant.

Measure latency, error rates, retake/uncertain rates, fallback frequency and catalog coverage.

Monitor aggregate metrics without logging raw photos or unnecessary sensitive data.

Keep rollback capability for model/catalog releases and document the model owner and release date.

# 14. Proposed repository structure

haircut-recommendation-engine/  
├── app/  
│   ├── main.py  
│   ├── api/                 # recommendations, catalog, feedback, health  
│   ├── schemas/             # request/response contracts  
│   ├── services/            # validation, fusion, face shape, ranking  
│   ├── repositories/        # storage interfaces  
│   └── security/            # limits, configuration, safe logging  
├── ml/  
│   ├── datasets/            # manifests only; do not commit restricted images  
│   ├── feature_pipeline.py  
│   ├── train.py  
│   ├── evaluate.py  
│   └── export_model.py  
├── catalog/                 # seed catalog and asset-rights manifest  
├── tests/  
│   ├── unit/  
│   ├── api/  
│   ├── ranking/  
│   └── privacy/  
├── migrations/  
├── scripts/                 # seed_catalog.py and data checks  
├── artifacts/               # model metadata; manage large files separately  
├── pyproject.toml  
├── Dockerfile  
├── compose.yaml             # optional for local services  
├── .env.example  
└── README.md

# 15. Development roadmap and phase acceptance

| Phase | Work | Acceptance evidence |  |
| --- | --- | --- |
| 1. Foundation | Repository, Python environment, FastAPI, Pydantic, pytest and schema draft. | App starts locally; health endpoints and schema tests pass. |  |
| 2. Source/licence audit | Inspect dataset labels, terms, image sources and code/model licences. | Dataset register completed; prohibited/unclear sources excluded. |  |
| 3. Three-view baseline | Capture guide, view-specific validation, feature definitions, fusion and uncertainty behavior. | Tests cover missing, poor and contradictory views; no unsupported features are fabricated. |  |
| 4. Hairstyle catalog | Define schema, seed styles, add compatibility tags and asset-rights records. | Catalog validation passes and every reference asset has a rights status. |  |
| 5. Rules-based recommender | Hard filters, ranking, reasons, fallback and baseline metrics. | Stable API output; reasons map to actual attributes; baseline evaluation report exists. |  |
| 6. Label collection | Consent flow, annotation guide, independent ratings and dataset versioning. | Quality-reviewed labels and participant-level split manifest. |  |
| 7. Model experiment | Train candidate ranker/classifier offline and compare with baselines. | Reproducible comparison report; no release without demonstrated benefit. |  |
| 8. Release preparation | Privacy/security review, deployment, monitoring, rollback and documentation. | Release checklist signed off; operational limits and limitations documented. |  |

# 16. Decisions still open

These are intentionally not treated as finalized until a small prototype or data audit provides evidence.

| Open decision | How to resolve it |  |
| --- | --- |
| Exact landmark model/package | Compare browser support, landmark reliability, licence, maintenance and performance on target devices. |  |
| Final feature definitions | Specify formulas and required landmarks; inspect failure cases across all three views. |  |
| Face-shape label guide | Write definitions, collect reviewer examples and measure inter-rater agreement. |  |
| Hair profile inputs | Decide which attributes are user-entered versus inferred; prefer user correction for uncertain texture/density. |  |
| Catalog size and source | Start with a manageable, rights-cleared catalog; expand after testing coverage. |  |
| Ranking labels and metric | Define a suitability rubric and select the primary metric before collecting labels. |  |
| Learned model family | Benchmark only after label structure, data quantity and baseline behavior are understood. |  |
| Production hosting/database | Choose after load, privacy, budget, latency and retention requirements are known. |  |
| Retention period and legal review | Set purpose-based retention, consent and deletion procedures before collecting real user photos. |  |

# 17. Known limitations and risks

Facial measurements can be inaccurate because of perspective, lighting, rotation, occlusion, facial hair or unsuitable view angles.

Three photos may not truly represent front and both side views; validation can reduce but not eliminate this risk.

Face-shape labels are subjective and vary by annotation convention.

Face shape alone cannot determine hairstyle suitability.

Hair texture, density, hairline and growth patterns may be difficult to infer from photos; ask the user when uncertain.

Stylists can disagree, and personal taste may differ from professional judgments.

Public datasets may have limited population coverage or restrictive licences.

A model can perform well on a familiar dataset and fail on real-world photos; held-out participant evaluation is essential.

Reference images cannot guarantee an identical result on another person.

Open-source tools can avoid paid inference fees, but do not guarantee free production hosting or zero operating cost.

The initial system excludes virtual try-on and live video.

# 18. Final technical decisions and conclusion

| Decision | Current plan |  |
| --- | --- |
| Primary language / API | Python + FastAPI + Pydantic. |  |
| Input | Three still photos: front, left side and right side. |  |
| Analysis | Browser-side JavaScript/TypeScript + MediaPipe where practical; exact package/model remains to be verified. |  |
| Multi-view method | Validate views independently; fuse only compatible reliable evidence; retain uncertainty. |  |
| Face-shape baseline | Geometry/rules with uncertain-result handling. |  |
| Recommendation baseline | Deterministic filtering and attribute-based ranking. |  |
| Learned model | Candidate CatBoost/scikit-learn ranker only after appropriate labels exist and testing demonstrates benefit. |  |
| Storage | SQLite for local prototype; PostgreSQL later only if justified. |  |
| Training | Offline, reproducible workflow; no public training endpoint. |  |
| Cost goal | ₹0 in paid AI API fees initially; total operating costs may not be zero. |  |
| Initial scope | Standalone engine; no website integration, virtual try-on or live video. |  |
| Release rule | Do not claim accuracy or release a learned model without independent evidence. |  |

Recommended next step: begin with a dataset/licence audit and a small technical spike for the three-view feature pipeline. Do not start by training a large model. First establish whether the chosen landmarks and capture instructions produce repeatable measurements, then build a transparent baseline and evaluation set.

Project status: planning and specification only. Code, datasets, licences, model performance, production security and deployment remain to be implemented or independently verified.

# 19. Recommended improvements and implementation priorities

The following improvements clarify implementation priorities for the planned engine. They are proposed actions, not completed features or validated performance claims.

1. Improve face-shape detection. Define exact landmark-based measurements, formulas, valid ranges and uncertainty rules. Test them on diverse, consented examples before finalizing classification thresholds.

2. Strengthen three-photo analysis. Validate front, left and right views separately. Combine only compatible, reliable measurements; flag contradictory views and request retakes when necessary.

3. Improve hairstyle recommendation quality. Rank styles using facial proportions together with hair texture, density, current/desired length, maintenance needs and stated preferences. Keep explanations linked to catalog attributes.

4. Build better evaluation datasets. Audit candidate dataset licences and quality. Collect consent-based three-view examples and independent hairstylist/user suitability judgments; split data by participant.

5. Capture user preferences and corrections. Ask about preferred length, desired look, excluded styles and styling time. Let users correct uncertain hair attributes and give optional feedback.

6. Handle low-confidence results safely. Use clear uncertain/partial results and actionable retake guidance rather than forcing a face-shape label or unsupported recommendation.

7. Evaluate and improve accuracy. Measure face-shape classification and hairstyle-ranking quality separately, using held-out participants and multiple reviewers. Compare any learned ranker against the rules baseline.

8. Optimize speed, privacy and cost. Benchmark performance on target devices; prefer local image analysis, minimize retention of photos and sensitive features, and maintain the initial ₹0 paid AI API fee goal while budgeting for other costs.

## Suggested implementation order

First validate three-view landmarks and facial measurements; then build a rights-cleared hairstyle catalog and rules-based ranker; next collect suitability ratings and evaluate the system; finally optimize deployment and consider learned ranking only when supported by evidence.
