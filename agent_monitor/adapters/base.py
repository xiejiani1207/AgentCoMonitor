"""框架适配器抽象接口。

每种 Agent 框架只需实现一个适配器，将框架原生事件转换为 TraceRecord。
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from agent_monitor.core.models import TraceRecord


class MonitoringAdapter(ABC):
    """监控适配器抽象基类。

    定义了监控平台与 Agent 框架之间的契约。适配器的职责：
    1. 在 Agent 生命周期事件触发时采集数据
    2. 将框架特有的事件格式转换为统一的 TraceRecord
    3. 通过回调将 TraceRecord 传递给监控平台
    """

    def __init__(self, on_trace: Callable[[TraceRecord], None] | None = None):
        """
        Args:
            on_trace: 回调函数，每完成一条 Trace 时调用。
                      监控采集模块通过此回调接收 Trace 数据。
        """
        self._on_trace = on_trace

    def set_on_trace(self, callback: Callable[[TraceRecord], None]) -> None:
        self._on_trace = callback

    def emit(self, trace: TraceRecord) -> None:
        if self._on_trace:
            self._on_trace(trace)

    @abstractmethod
    def get_framework_name(self) -> str:
        """返回框架名称，如 'langgraph'、'autogen'。"""
        ...
