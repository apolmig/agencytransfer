"""Network-free Inspect canary used by CI."""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import match
from inspect_ai.solver import generate


@task
def inspect_canary() -> Task:
    expected = "Default output from mockllm/model"
    return Task(
        dataset=[
            Sample(
                id=f"canary-{index}",
                input=f"Benign pipeline canary {index}. Return the configured mock response.",
                target=expected,
                metadata={"release_tier": "public", "purpose": "pipeline_only"},
            )
            for index in range(1, 4)
        ],
        solver=generate(),
        scorer=match(location="exact"),
        version="0.1.0",
        metadata={
            "construct": "pipeline integrity only",
            "non_claim": "This fixture does not measure model safety or capability.",
        },
    )
