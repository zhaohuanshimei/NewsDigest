"""Pipeline 状态跟踪数据类。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class StepResult:
    """单个 pipeline 步骤的执行结果。"""

    name: str
    status: Literal["success", "failed", "skipped"]
    duration_seconds: float
    count: int = 0
    error: str | None = None

    @property
    def is_success(self) -> bool:
        return self.status == "success"


@dataclass
class PipelineResult:
    """完整 pipeline 执行结果。"""

    started_at: datetime
    finished_at: datetime
    steps: list[StepResult] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def success(self) -> bool:
        """全部步骤成功才返回 True。"""
        return all(step.is_success for step in self.steps)

    def add_step(self, step: StepResult) -> None:
        self.steps.append(step)

    def get_step(self, name: str) -> StepResult | None:
        for step in self.steps:
            if step.name == name:
                return step
        return None
