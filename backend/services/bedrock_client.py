"""
AWS Bedrock LLM Client Service.

Supports multi-provider models (Anthropic Claude 3.5/Opus/Haiku, Amazon Nova,
Amazon Titan, Meta Llama) with dynamic payload formatting and automatic fallback.
"""

import json
import os
import boto3
from botocore.exceptions import BotoCoreError, ClientError

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
PRIMARY_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-sonnet-20241022-v2:0")

# Prioritized list of active Bedrock models across providers
MODEL_CANDIDATES = [
    PRIMARY_MODEL_ID,
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "amazon.nova-lite-v1:0",
    "amazon.nova-micro-v1:0",
    "amazon.titan-text-express-v1",
    "us.anthropic.claude-3-opus-20240229-v1:0",
    "meta.llama3-2-3b-instruct-v1:0",
]


def get_bedrock_runtime():
    """Initializes Bedrock runtime client for model invocation."""
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def get_bedrock_control():
    """Initializes Bedrock control plane client for metadata and model listing."""
    return boto3.client("bedrock", region_name=AWS_REGION)


def format_payload(model_id: str, prompt: str, system_prompt: str) -> dict:
    """Formats request payload based on model vendor."""
    lower_id = model_id.lower()

    if "anthropic" in lower_id or "claude" in lower_id:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }

    if "nova" in lower_id:
        return {
            "inferenceConfig": {"max_new_tokens": 1000, "temperature": 0.2},
            "system": [{"text": system_prompt}],
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
        }

    if "titan" in lower_id:
        return {
            "inputText": f"System: {system_prompt}\nUser: {prompt}\nAssistant:",
            "textGenerationConfig": {
                "maxTokenCount": 1000,
                "temperature": 0.2,
            },
        }

    if "meta" in lower_id or "llama" in lower_id:
        return {
            "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n",
            "max_gen_len": 512,
            "temperature": 0.2,
        }

    # Default Anthropic format fallback
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }


def parse_response(model_id: str, response_body: dict) -> str:
    """Extracts text response according to model vendor schema."""
    lower_id = model_id.lower()

    if "anthropic" in lower_id or "claude" in lower_id:
        return response_body["content"][0]["text"]

    if "nova" in lower_id:
        return response_body["output"]["message"]["content"][0]["text"]

    if "titan" in lower_id:
        results = response_body.get("results", [])
        if results:
            return results[0].get("outputText", "")
        return ""

    if "meta" in lower_id or "llama" in lower_id:
        return response_body.get("generation", "")

    # General fallback
    if "content" in response_body:
        return response_body["content"][0]["text"]
    return str(response_body)


def list_active_models() -> list[str]:
    """Queries AWS Bedrock control plane for available TEXT foundation models."""
    try:
        control = get_bedrock_control()
        res = control.list_foundation_models(byOutputModality="TEXT")
        summary_list = res.get("modelSummaries", [])
        return [m["modelId"] for m in summary_list if m.get("modelLifecycle", {}).get("status") == "ACTIVE"]
    except Exception as e:
        print(f"Failed to list foundation models from AWS Bedrock: {e}")
        return []


def query_bedrock_llm(prompt: str, system_prompt: str = "You are FleetGuard AI agent.") -> str:
    """Invokes AWS Bedrock model, trying active candidates with multi-vendor payloads."""
    client = get_bedrock_runtime()

    seen = set()
    candidates = [m for m in MODEL_CANDIDATES if not (m in seen or seen.add(m))]

    last_error = None
    for model_id in candidates:
        try:
            payload = format_payload(model_id, prompt, system_prompt)
            response = client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )

            response_body = json.loads(response["body"].read().decode("utf-8"))
            result_text = parse_response(model_id, response_body)
            print(f"[Bedrock Success] Invoked model: '{model_id}'")
            return result_text

        except (BotoCoreError, ClientError) as e:
            last_error = e
            print(f"[Bedrock Retry] Model '{model_id}' failed: {e}")
            continue

    return (
        f"Bedrock Error: All model candidates failed in region '{AWS_REGION}'. "
        f"Last error: {str(last_error)}. Ensure 'Model access' is granted in AWS Bedrock Console."
    )

