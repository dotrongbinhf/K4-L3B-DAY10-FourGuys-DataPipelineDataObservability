from .testset import build_test_set

__all__ = ["EvaluationBundle", "JudgeVerdict", "build_test_set", "evaluate_pipeline"]


def __getattr__(name: str):
    """Avoid importing optional, heavyweight evaluation dependencies for test-set creation."""
    if name in {"EvaluationBundle", "JudgeVerdict", "evaluate_pipeline"}:
        from .metrics import EvaluationBundle, JudgeVerdict, evaluate_pipeline

        exports = {
            "EvaluationBundle": EvaluationBundle,
            "JudgeVerdict": JudgeVerdict,
            "evaluate_pipeline": evaluate_pipeline,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
