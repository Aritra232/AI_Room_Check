# Property AI Inspection Service

FastAPI service for AI-powered property inspection.

## What it does

- Accepts one or more inspection photos as temporary input.
- Saves every analysis under `userId` and generated `roomId`.
- Generates and stores the inspection id automatically.
- Supports these inspection modules:
  - Interior
  - Exterior
  - Roof
  - HVAC
  - Water Heater
- Uses one analyze workflow for all modules:
  - `/api/users/{user_id}/inspections/{inspection_type}/analyze`
- Uses Gemini vision analysis for the interior module to inspect:
  - Ceiling
  - Walls
  - Windows
  - Floor
  - Electrical outlets
- Uses Gemini vision analysis for the exterior module to inspect:
  - Foundation
  - Siding/walls
  - Doors/windows
  - Drainage/gutters
  - Exterior cracks/moisture
- Uses Gemini vision analysis for the roof module to inspect:
  - Shingles/tiles
  - Flashing
  - Gutters
  - Chimney/vents
  - Sagging/leaks
- Uses Gemini vision analysis for the HVAC module to inspect:
  - Outdoor unit
  - Indoor unit
  - Ducting
  - Thermostat/wiring
  - Visible leaks/rust/damage
- Uses Gemini vision analysis for the water heater module to inspect:
  - Tank condition
  - Pipe connections
  - Pressure relief valve
  - Rust/corrosion
  - Leakage/drain pan/venting
- Returns structured JSON findings, severity counts, severity percentages, and risk score data for the inspection summary screen.
- Uses a dedicated Gemini damage-localization pass to draw only damaged patches onto the uploaded photo.
- Uploads annotated JPG files to AWS S3.
- Deletes temporary local files after the annotated JPG is uploaded.
- Stores analysis results in MongoDB.

The default vision model is `gemini-3.1-pro-preview`. You can override it with
`GEMINI_MODEL` in `.env` if your account uses a different model.

Required storage variables in `.env`:

```text
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_REGION=...
AWS_S3_BUCKET_NAME=...
```

## Setup

From the project root:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Docker

Build and run the API:

```powershell
docker compose up --build
```

The API will run at:

```text
http://127.0.0.1:7421
```

## Endpoints

```text
POST /api/users/{user_id}/inspections/{inspection_type}/analyze
GET  /api/users/{user_id}/inspections/{inspection_type}/{room_id}/analysis
POST /api/users/{user_id}/inspections/{inspection_type}/{room_id}/analysis/confirm
```

Supported `inspection_type` values:

```text
interior
exterior
roof
hvac
water_heater
```

In FastAPI Swagger docs, `inspection_type` appears as a dropdown with these values.

## Analyze Request

Use multipart form data:

```text
photos: one or more image files
```

Example:

```powershell
curl.exe -X POST "http://127.0.0.1:7421/api/users/user_123/inspections/interior/analyze" `
  -F "photos=@C:\path\to\room.jpg"
```

Example for another module:

```powershell
curl.exe -X POST "http://127.0.0.1:7421/api/users/user_123/inspections/roof/analyze" `
  -F "photos=@C:\path\to\roof.jpg"
```

The response includes `annotatedImageUrl` and `annotatedImages`, which point to JPG files uploaded to S3.
It also includes `userId`, `inspectionType`, the generated `roomId`, and `reportPreview` data for the Overview, Finding, and Recommendation tabs.
Raw bbox coordinates are used internally to create the annotated JPG, but they are not returned in the API response.
Uploaded original photos are stored only temporarily during analysis and are deleted after
the annotated JPG is uploaded to S3. `originalImageUrls` is returned as an empty list.
