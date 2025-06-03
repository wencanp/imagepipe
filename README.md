# ImagePipe
**ImagePipe** is a lightweight, cloud-native image processing platform. It supports image compression, format conversion, filter effects and OCR text recognition (currently English only), with a design focused on scalability and flexible deployment. Users can upload an image to trigger asynchronous processing and receive a download link upon completion.

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

## 📦 API Example
```bash
curl -X POST https://your-deployment-url/upload \
  -F "file=@test.jpg" \
  -F "process_type=convert"
```

## 📎 Live Demo
Try it out  on 👉 [Demo](https://imagepipe.up.railway.app/)  
Deployed on [Railway](https://railway.com/).

## 📄 License
MIT License