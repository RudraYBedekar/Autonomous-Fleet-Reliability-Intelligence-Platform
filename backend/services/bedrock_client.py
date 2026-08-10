import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Region from env or default to us-east-1
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
PRIMARY_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")

# Valid AWS Bedrock model IDs and US cross-region inference profile IDs
FALLBACK_MODEL_IDS = [
    PRIMARY_MODEL_ID,
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "us.anthropic.claude-3-opus-20240229-v1:0",
    "anthropic.claude-3-opus-20240229-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]

def get_bedrock_client():
    """Initializes Bedrock client using IAM Role or local AWS credentials."""
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)

def query_bedrock_llm(prompt: str, system_prompt: str = "You are FleetGuard AI agent.") -> str:
    """Invokes AWS Bedrock model using Anthropic Messages API structure."""
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

    last_error = None
    # Remove duplicates while preserving order
    seen = set()
    model_candidates = [m for m in FALLBACK_MODEL_IDS if not (m in seen or seen.add(m))]

    for model_id in model_candidates:
        try:
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload)
            )

            response_body = json.loads(response["body"].read().decode("utf-8"))
            return response_body["content"][0]["text"]

        except (BotoCoreError, ClientError) as e:
            last_error = e
            print(f"Bedrock invocation failed for model '{model_id}': {e}")
            continue

    return f"Bedrock Error: All candidate models failed. Last error: {str(last_error)}"
