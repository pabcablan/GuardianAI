from infrastructure.adapters.anonymization.api_anonymizer import ApiAnonymizer
from infrastructure.ports.anonymizer import Anonymizer

class AnonymizerProvider:
    def __init__(self, use_api: bool, **kwargs):
        self.use_api = use_api
        self.kwargs = kwargs
        self._cache = {}

    def get_anonymizer(self, model_alias: str = None) -> Anonymizer:
        if self.use_api:
            if model_alias not in self._cache:
                self._cache[model_alias] = ApiAnonymizer(api_url=self.kwargs['api_url'], model_name=model_alias,
                    client=self.kwargs.get('client'))
            return self._cache[model_alias]
        
        else:
            from infrastructure.adapters.anonymization.llm_anonymizer import LlmAnonymizer

            return LlmAnonymizer(model=self.kwargs['model'], tokenizer=self.kwargs['tokenizer'])
