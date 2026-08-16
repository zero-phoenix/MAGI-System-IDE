"""Banco de evaluación (Plan MAGI 9.0 §3.5)."""
from .bench import (
    BenchResult,
    Comparison,
    EvalBench,
    EvalTask,
    TaskOutcome,
    compare,
    default_bench,
)

__all__ = ["BenchResult", "Comparison", "EvalBench", "EvalTask", "TaskOutcome",
           "compare", "default_bench"]
