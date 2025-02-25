import os
import boto3
from botocore.exceptions import ClientError

def get_secret():
    secret_name = "gcs/secrets/lucano"  # Your secret name in AWS Secrets Manager
    region_name = "us-east-2"            # Your region

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        return get_secret_value_response['SecretString']
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        raise e

def setup_google_credentials():
    # Retrieve the secret (JSON string)
    gcp_creds_json = get_secret()
    # Write it to a temporary file (AWS environments allow /tmp)
    temp_path = "/tmp/google_creds.json"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(gcp_creds_json)
    # Optionally, print a message
    print("Google credentials written to", temp_path)
    # (Don't forget to set the environment variable if needed)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path

if __name__ == "__main__":
    setup_google_credentials()