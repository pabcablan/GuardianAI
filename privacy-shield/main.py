from infrastructure.adapters.model_loader.transformers_provider import TransformersProvider
from infrastructure.adapters.model_loader.unsloth_provider import UnslothProvider


def main():
    trans_provider = TransformersProvider()
    unsloth_provider = UnslothProvider()

    model_eval, tok_eval = trans_provider.load(model_id="Qwen/Qwen3.5-0.8B-Base",  name="evaluator_model",  gpu_index=0)
    model_anon, tok_anon = unsloth_provider.load(model_id="unsloth/Qwen3.5-0.8B-Base",  name="anonymizer_model")

if __name__ == "__main__":
    main()