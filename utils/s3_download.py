# import requests
# import io
# import logging
# from flask import send_file

# logging.basicConfig(level=logging.INFO)

# def fetch_file_from_presigned_url(url, download_name=None):
#     try:
#         logging.info(f"[UTILS] Fetching file from: {url}")
#         response = requests.get(
#             url,
#             stream=True,
#             headers={'User-Agent': 'ImagePipe'}
#         )
#         response.raise_for_status()

#         return send_file(
#             io.BytesIO(response.content),
#             as_attachment=True,
#             download_name=download_name or 'downloaded_file'
#         )
#     except Exception as e:
#         logging.error(f"[UTILS] Failed to download from MinIO: {e}")
#         raise RuntimeError(f"Failed to fetch file: {e}")
