<div align="center">
  <h1>ImagePipe</h1>
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://choosealicense.com/licenses/mit/)

</div>

**ImagePipe** is a lightweight, cloud-native image processing platform. It supports image compression, format conversion, filter effects and OCR text recognition (currently English only), with a design focused on scalability and flexible deployment. Users can upload an image to trigger asynchronous processing and receive a download link upon completion.

Try it out  on 👉 [Demo](https://imagepipe.up.railway.app/)  
Deployed on [Railway](https://railway.com/).

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

## 📦 API
### Base Endpoint and Example
```bash
curl -X POST https://imagepipe.up.railway.app/api/upload \
  -F "file=@test.jpg" \
  -F "process_type=convert" \
```
### Parameters
1. **Conversion/Compress** (process_type=convert)
  - convert_type: choose from ['.jpeg', '.png', '.gif', '.bmp']
  - quality: int from 1-95
2. **Filter** (process_type=filter)
  - filter_type: choose from ['BLUR', 'CONTOUR', 'DETAIL', SHARPEN']
3. **OCR** (process_type=ocr)