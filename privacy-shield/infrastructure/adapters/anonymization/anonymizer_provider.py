from infrastructure.adapters.anonymization.api_anonymizer import ApiAnonymizer
from infrastructure.adapters.anonymization.optimized_api_anonymizer import OptimizedApiAnonymizer
from infrastructure.adapters.anonymization.llm_anonymizer import LlmAnonymizer
from infrastructure.ports.anonymizer import Anonymizer

class AnonymizerProvider:
    def __init__(self, use_api: bool, optimized: bool = False, **kwargs):
        self.use_api = use_api
        self.optimized = optimized
        self.kwargs = kwargs
        self._cache = {}

    def get_anonymizer(self, model_alias: str = None) -> Anonymizer:
        if self.use_api:
            cache_key = f"{model_alias}_opt" if self.optimized else f"{model_alias}_std"
            
            if cache_key not in self._cache:
                anonymizer_class = OptimizedApiAnonymizer if self.optimized else ApiAnonymizer
                
                self._cache[cache_key] = anonymizer_class(api_url=self.kwargs['api_url'], model_name=model_alias,
                    client=self.kwargs.get('client'))
            
            return self._cache[cache_key]
        
        else:
            from infrastructure.adapters.anonymization.llm_anonymizer import LlmAnonymizer

            return LlmAnonymizer(model=self.kwargs['model'], tokenizer=self.kwargs['tokenizer'])
