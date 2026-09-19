import os
import json
import re
import logging
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError

logger = logging.getLogger("recallmatch.bedrock")


class BedrockClient:
    """
    Reusable client abstraction for Amazon Bedrock runtime API.
    
    Requirements:
    - boto3 client for bedrock-runtime
    - AWS_REGION and BEDROCK_MODEL_ID loaded from environment configuration
    - Graceful fallback on missing credentials, configuration issues, API timeouts/errors
    - Structured JSON output parsing
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                self._client = boto3.client(
                    service_name="bedrock-runtime",
                    region_name=self.region_name,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize boto3 Bedrock client: {e}")
                self._client = None
        return self._client

    def invoke_structured(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Invokes Bedrock model and parses the returned JSON payload into a dictionary.
        Returns None gracefully on missing credentials, configuration issues, API failures, or malformed JSON.
        """
        client = self._get_client()
        if not client:
            logger.warning("Bedrock client is not available or boto3 client initialization failed.")
            return None

        try:
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            kwargs: Dict[str, Any] = {
                "modelId": self.model_id,
                "messages": messages,
                "inferenceConfig": {"temperature": 0.0, "maxTokens": 1000},
            }
            if system_prompt:
                kwargs["system"] = [{"text": system_prompt}]

            response = client.converse(**kwargs)
            output_text = response["output"]["message"]["content"][0]["text"]
            return self._extract_json(output_text)

        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.warning(f"Bedrock AWS credentials missing or incomplete: {e}")
            return None
        except (ClientError, BotoCoreError) as e:
            logger.warning(f"Bedrock API invocation failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error during Bedrock invocation: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON object from response text, handling markdown code fences or extra commentary."""
        if not text:
            return None

        clean_text = text.strip()
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            pass

        # Match markdown ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", clean_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Match outer braces
        match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Could not parse valid JSON from Bedrock model output: {clean_text[:200]}")
        return None
