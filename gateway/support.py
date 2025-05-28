import time
from datetime import datetime, timedelta

from urllib.parse import urlparse, parse_qs

def is_minio_url_expired(url):
    """ Check if a MinIO presigned URL has expired."""
    try:
        print("enter is_minio_url_expired")
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        print("check query")
        expires_in = int(query.get('X-Amz-Expires', [0])[0])
        signed_time_str = query.get('X-Amz-Date', [None])[0]
        print("check signed_time_str")
        if not signed_time_str:
            return True  # cannot determine expiry, assume expired
        print("check expires time")
        signed_time = datetime.strptime(signed_time_str, "%Y%m%dT%H%M%SZ")
        expiry_time = signed_time + timedelta(seconds=expires_in)

        return time.time() > expiry_time.timestamp()
    except Exception as e:
        return True  # if any error occurs, assume expired
