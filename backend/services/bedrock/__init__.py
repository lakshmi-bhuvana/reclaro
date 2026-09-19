"""
Bedrock integration module for RecallMatch.
Provides Amazon Bedrock client abstraction, structured normalization, and candidate generation.
"""

from backend.services.bedrock.bedrock_client import BedrockClient
from backend.services.bedrock.normalization_service import BedrockNormalizationService, BedrockNormalizationOutput
from backend.services.bedrock.candidate_service import BedrockCandidateService

__all__ = [
    "BedrockClient",
    "BedrockNormalizationService",
    "BedrockNormalizationOutput",
    "BedrockCandidateService",
]
