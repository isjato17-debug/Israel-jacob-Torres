"""Retained OpenAI-compatible request contract. Live transport is approval-blocked."""
import json
import os


class LiveUsageNotAuthorized(RuntimeError):
    pass


class AIProvider:
    def __init__(self):
        self.provider=os.getenv('GENESIS_AI_PROVIDER','disabled').lower()
        self.api_key=os.getenv('GENESIS_AI_API_KEY','')
        self.base_url=os.getenv('GENESIS_AI_BASE_URL','')
        self.model=os.getenv('GENESIS_AI_MODEL','')
    def enabled(self):
        # Live activation requires a separately reviewed authorization/budget change.
        # Credentials or environment flags alone can never authorize a paid request.
        return False
    def structured_analysis(self, system_prompt, payload):
        raise LiveUsageNotAuthorized("Live AI is awaiting explicit owner authorization")
    def _authorized_transport(self, system_prompt, payload):
        # No network implementation can run in this phase, including direct calls.
        raise LiveUsageNotAuthorized("Live AI transport is disabled")
    def build_request(self, system_prompt, payload):
        """Offline contract builder for a future reviewed, budget-reserving transport."""
        return {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': json.dumps(payload)},
            ],
            'response_format': {'type': 'json_object'}, 'temperature': 0.2,
            'max_tokens': 1200,
        }


ai_provider=AIProvider()
