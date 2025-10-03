import os
import logging

# Reduce logging noise from azure SDK HTTP policy and storage modules.
logging.basicConfig(level=logging.WARNING)
logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.WARNING)
logging.getLogger('azure.storage.blob').setLevel(logging.WARNING)

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
load_dotenv()  # loads variables from a .env file into the environment


def upload_file_to_blob(blob_container_name: str, blob_output_path: str, file_path: str, file_name: str) -> str:
    """
    Upload a local file to Azure Blob Storage under the path specified by EVAL_BLOB_OUTPUT_PATH.

    Args:
        file_path: Local path to the file to upload (including filename or directory).
        file_name: Name to use for the file in blob storage (will be placed under the output path).
                   If file_path points to a file, file_name can be the same as os.path.basename(file_path).

    Returns:
        The full blob URL of the uploaded file.

    Raises:
        FileNotFoundError: If the local file does not exist.
        EnvironmentError: If required env variables are missing.
        Exception: Propagates other upload errors.
    """
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = blob_container_name
    blob_output_path = blob_output_path

    if not connection_string or not container_name or not blob_output_path:
        raise EnvironmentError("AZURE_STORAGE_CONNECTION_STRING, EVAL_BLOB_CONTAINER_NAME and EVAL_BLOB_OUTPUT_PATH must be set in environment")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Local file not found: {file_path}")

    # normalize blob name
    blob_prefix = blob_output_path.rstrip('/')
    blob_name = f"{blob_prefix}/{file_name}" if blob_prefix else file_name

    # create clients
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)
    blob_client = container_client.get_blob_client(blob_name)

    try:
        with open(file_path, 'rb') as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"Uploaded local file '{file_path}' to blob '{blob_name}' in container '{container_name}'")
    except Exception as ex:
        # Map SDK errors if needed by class name
        raise

    # return the blob URL
    return blob_client.url


if __name__ == "__main__":
    # quick local test (will raise if env not configured)
    test_path = "src/evaluations/offline/bill_item_eval/report/inferenceModelNameType.GPT_41_MINI.json"
    test_name = "inferenceModelNameType.GPT_41_MINI.json"
    blob_container_name = "slm-data"
    blob_output_path = "slm_training/eval/evaluation_output/"
    try:
        url = upload_file_to_blob(blob_container_name, blob_output_path, test_path, test_name)
        print(f"Uploaded to: {url}")
    except Exception as e:
        print(f"Upload failed: {e}")
        raise