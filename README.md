<div align="center">
  <h1>ImagePipe</h1>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://choosealicense.com/licenses/mit/)
</div>

**ImagePipe** is a lightweight, cloud-native image processing platform. It supports image compression, format conversion, filter effects and OCR text recognition (currently English only), with a design focused on scalability and flexible deployment. Users can upload an image to trigger asynchronous processing and receive a download link upon completion.

Try it out on 👉 [Railway Demo](https://imagepipe.up.railway.app/)  
More dev details in [README.dev](./README.dev.md)


## ✨ Features
- Image upload & processing (convert / filter / OCR - English only)
- Asynchronous task handling (Celery + Redis)
- Cloud-compatible storage (MinIO, S3-compatible)
- Docker-based containerized deployment
- Live deployment on Railway
- RESTful API interface

## 🧰 Tech Stack
- **Backend**: Python, Flask, Celery, Redis  
- **Object Storage**: MinIO (S3-compatible)  
- **Database**: PostgreSQL  
- **Containerization**: Docker  
- **Deployment Platforms**: Railway (dev) 
- **Frontend**: React

## 📦 RESTful API

Base URL: `https://imagepipe.up.railway.app/api`

---

### POST `/upload`
Upload an image and submit a processing task.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | Image file to process (max 16MB) |
| `process_type` | string | ✅ | `convert` / `filter` / `ocr` |
| `convert_type` | string | convert only | `.jpeg` `.png` `.gif` `.bmp` |
| `quality` | int | convert only | Compression quality `1-95` (default: 60) |
| `filter_type` | string | filter only | `BLUR` `CONTOUR` `DETAIL` `SHARPEN` |

**Response** `200 OK`
```json
{
  "success": true,
  "message": "[SUCCESS] Conversion task submitted",
  "task_id": "f9432f84-368a-42d1-ace3-981e4fe6c71a"
}
```

**Example**
```bash
curl -X POST https://imagepipe.up.railway.app/api/upload \
  -F "file=@photo.jpg" \
  -F "process_type=convert" \
  -F "convert_type=.png" \
  -F "quality=80"
```

---

### GET `/status/<task_id>`
Poll the status of a submitted task.

**Response** `200 OK`
```json
{
  "success": true,
  "message": "SUCCESS",
  "task_id": "f9432f84-368a-42d1-ace3-981e4fe6c71a"
}
```

| Status | Meaning |
|--------|---------|
| `PENDING` | Task is queued, waiting for a worker |
| `SUCCESS` | Task completed, result is ready |
| `FAILURE` | Task failed during processing |

---

### GET `/download/task/<task_id>`
Retrieve the presigned download URL for a completed task.

**Response** `200 OK`
```json
{
  "success": true,
  "url": "https://bucket.s3.amazonaws.com/convert/output.png?X-Amz-Signature=..."
}
```

**Error Responses**

| Code | Meaning |
|------|---------|
| `404` | Task not found |
| `404` | Task completed but no result file available |

---

### POST `/cleanup`
Manually trigger cleanup of expired files (older than 12 hours) from storage and database.

**Response** `200 OK`
```json
{
  "success": true,
  "message": "[SUCCESS] Cleanup task triggered",
  "task_id": "a1b2c3d4-..."
}
```