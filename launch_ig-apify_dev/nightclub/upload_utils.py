import os
import requests
from google.cloud import storage

def upload_image_to_gcs(image_url: str, bucket_name: str, destination_blob_name: str) -> str:
    """
    Downloads an image from image_url and uploads it to the specified GCS bucket.
    Returns the public URL of the uploaded image.
    """
    # Download the image data
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {image_url}")
    image_data = response.content

    # Initialize the GCS client (credentials are taken from GOOGLE_APPLICATION_CREDENTIALS env variable)
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload the image data
    blob.upload_from_string(image_data, content_type=response.headers.get("Content-Type"))

    # Because uniform bucket-level access is enabled, we can’t use legacy ACLs.
    # Ensure your bucket’s IAM policy grants public read (roles/storage.objectViewer for allUsers).
    # Construct the public URL manually:
    public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    return public_url

if __name__ == "__main__":
    bucket_name = os.environ.get("GCS_BUCKET_NAME", "your-unique-bucket-name")
    test_image_url = "https://example.com/some-image.jpg"
    destination_blob = "images/test-image.jpg"
    public_url = upload_image_to_gcs(test_image_url, bucket_name, destination_blob)
    print("Public URL:", public_url)
