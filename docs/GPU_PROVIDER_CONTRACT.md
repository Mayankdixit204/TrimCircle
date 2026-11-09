# TrimCircle GPU provider contract

The web application and queue are independent of the final generation model. A GPU provider needs one HTTPS endpoint.

## Request

`POST $TRIMCIRCLE_GPU_ENDPOINT`

Multipart fields:

- `image`: normalized PNG, maximum dimension 1536 pixels
- `style_id`: catalog hairstyle identifier
- `color`: requested hair colour
- `texture`: requested hair texture

When `TRIMCIRCLE_GPU_TOKEN` is configured, the worker sends `Authorization: Bearer <token>`.

## Successful response

- HTTP `200`
- `Content-Type: image/png` or another `image/*` type
- Body: generated hairstyle result

The provider must preserve facial identity, pose, expression, clothing, lighting, and background. Only the hair region may change.

## Failure response

Return a non-2xx status with a short error message. The worker marks the job as failed without exposing the source image through logs.

## Worker

Process one job:

```powershell
python worker.py
```

Continuously process jobs:

```powershell
python worker.py --watch --interval 5
```

Do not start the worker until the private endpoint and token have been verified. Jobs and images expire after 24 hours by default.
