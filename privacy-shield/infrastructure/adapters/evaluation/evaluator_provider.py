from infrastructure.adapters.evaluation.api_evaluator import ApiEvaluator
from infrastructure.adapters.evaluation.qwen_evaluator import QwenEvaluator
from infrastructure.ports.anonymization_evaluator import AnonymizationEvaluator

class EvaluatorProvider:
    def __init__(self, use_api: bool, **kwargs):
        self.use_api = use_api
        self.kwargs = kwargs
        self._cache = {}

    def get_evaluator(self, model_alias: str = None) -> AnonymizationEvaluator:
        if self.use_api:
            if model_alias not in self._cache:
                self._cache[model_alias] = ApiEvaluator(api_url=self.kwargs['api_url'], model_name=model_alias,
                                                            client=self.kwargs.get('client'))
            return self._cache[model_alias]
        
        else:
            return QwenEvaluator(model=self.kwargs['model'], tokenizer=self.kwargs['tokenizer'])