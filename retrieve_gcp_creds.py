import time
import os
import boto3
from botocore.exceptions import ClientError

def get_secret():
    secret_name = "gcs/secrets/lucano"  # Your secret name in AWS Secrets Manager
    region_name = "us-east-2"            # Your region

    print("→ Starting secret retrieval from AWS Secrets Manager...")
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        start_time = time.time()
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        elapsed = time.time() - start_time
        print(f"→ Secret successfully retrieved in {elapsed:.2f} seconds.")
        return get_secret_value_response['SecretString']
    except ClientError as e:
        print(f"‼️ Error retrieving secret: {e}")
        raise e

def setup_google_credentials():
    print("→ Setting up Google credentials...")
    # Retrieve the secret (JSON string)
    gcp_creds_json = get_secret()
    
    # Write the secret to a temporary file (AWS environments allow /tmp)
    temp_path = "/tmp/google_creds.json"
    print(f"→ Writing credentials to temporary file at {temp_path}...")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(gcp_creds_json)
    print("→ Credentials written to temporary file.")

    # Set the environment variable so that other processes can pick it up.
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
    print(f"→ Environment variable GOOGLE_APPLICATION_CREDENTIALS set to {temp_path}")

if __name__ == "__main__":
    print("=== Starting Google credentials setup ===")
    setup_google_credentials()
    print("=== Google credentials setup completed ===")
