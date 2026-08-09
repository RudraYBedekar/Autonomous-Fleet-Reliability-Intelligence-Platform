import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Region from env or default to us-east-1
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-4-6")

def get_bedrock_client():
    """Initializes Bedrock client using IAM Role or local AWS credentials."""
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)

def query_bedrock_llm(prompt: str, system_prompt: str = "You are FleetGuard AI agent.") -> str:
    """Invokes AWS Bedrock model using Anthropic Messages API structure."""
    try:
        client = get_bedrock_client()
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.2
        }

        response = client.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )

        response_body = json.loads(response["body"].read().decode("utf-8"))
        return response_body["content"][0]["text"]

    except (BotoCoreError, ClientError) as e:
        print(f"Bedrock API error: {e}")
        return f"Bedrock Error: {str(e)}"
