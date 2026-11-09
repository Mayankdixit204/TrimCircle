# Architecture and implementation roadmap

## Target data flow

1. Decode and EXIF-normalize each bounded upload.
2. Validate format, dimensions, exposure, sharpness, face count, visibility, and expected pose.
3. Extract landmarks while preserving the original coordinate reference.
4. Produce measurements with validity, quality, view, unit, and limitation.
5. Fuse only compatible valid evidence: front widths remain front-only and profile evidence remains profile-specific.
6. Classify with abstention/uncertainty and preserve user correction separately.
7. Filter infeasible styles, rank compatible candidates, diversify the top five, and explain the actual factors.
8. Store raw photos only for consented try-on jobs protected by owner and worker credentials and expiry.

## Ordered roadmap

| Phase | Dependency | Complexity | Acceptance evidence |
|---|---|---:|---|
| Audit and baseline | none | S | Audit and recorded test baseline |
| Image and geometry correctness | audit | M | Coordinate, aspect-ratio, EXIF, and structured-measurement tests |
| Pose and multi-view fusion | geometry | L | Labelled pose set and front-only comparison |
| Face-shape validation | fusion | L | Person-disjoint evaluation and documented dataset license |
| Knowledge base and ranking | stable profile schema | L | Constraint tests and independent stylist NDCG@5 ratings |
| Try-on security | identity/session choice | M | Cross-owner, worker-auth, expiry, traversal, and upload tests |
| Performance | stable pipeline | M | Reproducible latency and peak-memory script |
| Production release | all prior phases | M | Deployment, limitations, security review, and measured results |

## Validation plan

Use consented or legally licensed data only. Record subject/group IDs so no person or near-duplicate crosses train, validation, and test splits. Compare the historical rule, corrected front geometry, and multi-view fusion on the same held-out set. Report failure and abstention with accuracy, macro F1, per-class metrics, and confusion matrices. Report probabilities only after held-out calibration. Recommendation quality requires independent human relevance judgements; rule scores are not labels.
