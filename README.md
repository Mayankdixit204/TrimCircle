# TrimCircle Haircut Recommendation MVP

A lightweight, explainable haircut recommendation prototype designed to run on a 4 GB RAM computer.

## What works

- Guided live-camera capture for front, left, and right views
- Live single-face, centering, face-size, and approximate pose guidance
- Server-side file, size, resolution, exposure, and blur validation
- MediaPipe facial-landmark analysis with user confirmation
- Hair texture, density, length, and maintenance profile
- Rules-based ranking from a rights-aware hairstyle catalog
- Plain-language reasons and compatibility scores
- FastAPI API and responsive browser interface
- No paid AI API, Docker, database server, or GPU required

Facial geometry is estimated from MediaPipe landmarks and disclosed as experimental. Users can confirm or change the estimate before ranking.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

Camera capture requires a secure browser context. It works on `localhost` during local development and must use HTTPS when deployed.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## API

- `GET /health`
- `GET /v1/hairstyles`
- `POST /v1/validate-photos`
- `POST /v1/capture-check`
- `POST /v1/analyze-face`
- `POST /v1/recommendations`
- Interactive API documentation: <http://127.0.0.1:8000/docs>

## Low-memory operation

Photos are opened and analyzed one at a time. The server does not retain uploads, and images are closed immediately after analysis.

## Virtual try-on handoff

Each recommendation includes **Preview on my face**. The local workflow:

1. Select a recommended hairstyle and hair colour.
2. Download the private Kaggle generation ZIP.
3. Upload the ZIP to the future private Kaggle workflow.
4. Generate `result.png`.
5. Import the result into TrimCircle for before/after comparison and download.

The ZIP contains `input.png`, `job.json`, `prompt.txt`, and privacy instructions. No uploaded or generated image is persisted by the FastAPI application.

- `POST /v1/tryon/prepare` — validates and packages a private generation job

## Asynchronous live architecture

The local implementation now includes:

- SQLite-backed try-on jobs
- 24-hour automatic expiry
- Status and progress polling
- Result upload/download
- Explicit deletion of source and result images
- Manual Kaggle ZIP fallback
- Generic authenticated GPU HTTP provider
- Standalone queue worker

The browser can create a secure job immediately. Until a GPU endpoint is configured, the job remains in `awaiting_gpu` and the manual private-Kaggle package remains available.

See `docs/GPU_PROVIDER_CONTRACT.md` for the production provider contract.

## Three-view 2D try-on

The default on-device preview no longer requires Kaggle or a cloud GPU. It uses MediaPipe anchors and transparent WebP overlays rendered with HTML Canvas.

Implemented controls:

- Independent front, left, and right placement
- Automatic face-width, hairline, center, and rotation anchors
- Direct touch/mouse dragging
- Size, rotation, opacity, and position controls
- Natural, black, brown, blonde, and copper colour treatments
- Per-view reset
- Individual and three-view downloads
- Editable fallback placement when a profile face is not detected

A prepared Textured Crop three-view asset is included under `app/static/hairstyles/textured-crop/`. Additional catalog styles need matching `front.webp`, `left.webp`, `right.webp`, and `metadata.json` assets.

To open the photo-free editor demonstration, visit:

`http://127.0.0.1:8000/?demo2d=1`
