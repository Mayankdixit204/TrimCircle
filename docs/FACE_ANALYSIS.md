# Face analysis

TrimCircle uses MediaPipe Face Landmarker as a landmark source. It does not treat landmarks as exact anatomical boundaries.

Normalized coordinates are converted to original-image pixels before distance calculation:

`dx = (x2 - x1) * width`, `dy = (y2 - y1) * height`, `distance = sqrt(dx^2 + dy^2)`.

The API returns measurements with value, unit, source view, quality, validity, and limitation. Front ratios use face-height, cheek-span, forehead-span, jaw-span, and chin-span proxies. Profile views currently contribute a nose-to-chin/profile-height proxy. Profile metrics are not substituted for frontal widths.

Face-shape labels are styling categories. Current thresholds are an unvalidated transparent baseline. Responses return an uncertainty label and possible alternative, not a percentage. Users can confirm or correct the result. No real-world accuracy claim is made.
