# Room AI Inspection Service

FastAPI service for AI-powered room inspection.

## What it does

- Accepts one or more room photos as temporary input.
- Saves every analysis under `userId` and generated `roomId`.
- Generates and stores the room id automatically.
- Infers the room name/type from the photo when possible.
- Uses Gemini vision analysis to inspect:
  - Ceiling
  - Walls
  - Windows
  - Floor
  - Electrical outlets
- Returns structured JSON findings, severity counts, severity percentages, and risk score data for the inspection summary screen.
- Uses a dedicated Gemini damage-localization pass to draw only damaged patches onto the uploaded photo.
- Uploads annotated JPG files to AWS S3.
- Deletes temporary local files after the annotated JPG is uploaded.
- Stores analysis results in MongoDB.

The default vision model is `gemini-3.8-flash`. You can override it with
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
http://127.0.0.1:8000
```

## Endpoints

```text
POST /api/users/{user_id}/rooms/analyze
GET  /api/users/{user_id}/rooms/{room_id}/analysis
POST /api/users/{user_id}/rooms/{room_id}/analysis/confirm
```

## Analyze Request

Use multipart form data:

```text
photos: one or more image files
```

Example:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/users/user_123/rooms/analyze" `
  -F "photos=@C:\path\to\room.jpg"
```

The response includes `annotatedImageUrl` and `annotatedImages`, which point to JPG files uploaded to S3.
It also includes `userId`, the generated `roomId`, and `reportPreview` data for the Overview, Finding, and Recommendation tabs.
Raw bbox coordinates are used internally to create the annotated JPG, but they are not returned in the API response.
Uploaded original photos are stored only temporarily during analysis and are deleted after
the annotated JPG is uploaded to S3. `originalImageUrls` is returned as an empty list.
