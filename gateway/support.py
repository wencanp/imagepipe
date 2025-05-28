import time

from urllib.parse import urlparse, parse_qs

def is_minio_url_expired(url):
    """ Check if a MinIO presigned URL has expired."""
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        expires_in = int(query.get('X-Amz-Expires', [0])[0])
        signed_time_str = query.get('X-Amz-Date', [None])[0]

        if not signed_time_str:
            return True  # cannot determine expiry, assume expired

        from datetime import datetime, timedelta
        signed_time = datetime.strptime(signed_time_str, "%Y%m%dT%H%M%SZ")
        expiry_time = signed_time + timedelta(seconds=expires_in)

        print(f"signed_time: {signed_time}, expiry_time: {expiry_time}")
        return time.time() < expiry_time.timestamp()
    except Exception as e:
        return True  # if any error occurs, assume expired
