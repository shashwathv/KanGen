import boto3 
import os 
from pathlib import Path

s3 = boto3.client('s3', region_name='us-east-1')
BUCKET = os.getenv("S3_BUCKET", "kangen-storage")

def upload_file(local_path: str, s3_key:str) -> bool:
    try:
        s3.upload_file(local_path, BUCKET, s3_key)
        return True
    except Exception as e:
        print(f"Upload failed: {e}")
        return False
    
def download_file(s3_key: str, local_path: str) -> bool:
    try:
        s3.download_file(BUCKET, s3_key, local_path)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def get_presigned_url(s3_key: str, expiry: int=3600) -> str:
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET, 'Key': s3_key},
            ExpiresIn=expiry
        )   
        return url
    except Exception as e:
        print(f"Presigned url failed: {e}")
        return ""
    
def delete_file(s3_key: str) -> bool:
    try:
        s3.delete_object(Bucket=BUCKET, Key=s3_key)
        return True
    except Exception as e:
        print(f"Delete failed: {e}")
        return False
    