"""LangGraph 适配器——通过 astream_events 零侵入采集 Trace 数据。

LangGraph 1.x 的节点事件通过 `graph.astream_events()` 暴露（节点名在
metadata.langgraph_node），旧的 config["callbacks"] 逐节点回调不再可靠。
"""

import json
import uuid
from datetime import datetime
from typing import Any

from agent_monitor.adapters.base import MonitoringAdapter
from agent_monitor.core.models import TraceRecord, TraceStatus

# 输入/输出序列化截断长度，避免超大 state（如 60 日日线）撑爆数据库
_MAX_SERIALIZE_LEN = 2000


class LangGraphCallback(MonitoringAdapter):
    """LangGraph 监控适配器。

    通过 astream_events 采集每个节点的执行 Trace，Demo 端无需 import agent_monitor。

    用法:
        monitor = LangGraphCallback(on_trace=my_handler)
        await monitor.run(graph, {"query": "..."})
    """

    def __init__(self, on_trace=None):
        super().__init__(on_trace)
        self._task_id: str | None = None
        self._active: dict[str, TraceRecord] = {}   # node name -> 进行中的 Trace
        self._trace_ids: dict[str, str] = {}        # node name -> trace_id
        self._parent_map: dict[str, str] = {}       # node name -> 父节点名

    def get_framework_name(self) -> str:
        return "langgraph"

    async def run(self, graph, input: dict, config: dict | None = None) -> dict:
        """运行 graph，采集每个节点的 Trace 并返回最终状态。"""
        # 一次 graph 运行 = 一个 task；每个节点有独立的 run_id（trace_id）
        self._task_id = str(uuid.uuid4())
        self._active = {}
        self._trace_ids = {}
        self._parent_map = self._build_parent_map(graph)
        final_state: dict = {}

        async for event in graph.astream_events(input, version="v2", config=config):
            metadata = event.get("metadata") or {}
            name = metadata.get("langgraph_node")
            if name:
                kind = event["event"]
                if kind == "on_chain_start":
                    self._on_node_start(name, event)
                elif kind == "on_chain_end":
                    self._on_node_end(name, event)
                elif kind == "on_chain_error":
                    self._on_node_error(name, event)
            elif event["event"] == "on_chain_end":
                # 图级结束事件：携带最终状态
                output = event.get("data", {}).get("output")
                if isinstance(output, dict):
                    final_state = output

        return final_state

    # ---- 内部 ----

    def _build_parent_map(self, graph) -> dict[str, str]:
        """从图拓扑提取每个节点的父节点（多父节点取第一个）。"""
        parent_map: dict[str, str] = {}
        for edge in graph.get_graph().edges:
            if edge.source == "__start__" or edge.target == "__end__":
                continue
            parent_map.setdefault(edge.target, edge.source)
        return parent_map

    def _on_node_start(self, name: str, event: dict) -> None:
        trace_id = str(event["run_id"])
        trace = TraceRecord(
            trace_id=trace_id,
            task_id=self._task_id or str(uuid.uuid4()),
            agent_name=name,
            agent_role="",
            input_prompt=self._serialize(event.get("data", {}).get("input", {})),
            output_content="",
            start_time=datetime.utcnow(),
            parent_trace_id=self._trace_ids.get(self._parent_map.get(name, "")),
        )
        self._active[name] = trace
        self._trace_ids[name] = trace_id

    def _on_node_end(self, name: str, event: dict) -> None:
        trace = self._active.pop(name, None)
        if trace is None:
            return
        trace.end_time = datetime.utcnow()
        trace.output_content = self._serialize(event.get("data", {}).get("output", {}))
        if trace.start_time:
            trace.duration_ms = int(
                (trace.end_time - trace.start_time).total_seconds() * 1000
            )
        trace.status = TraceStatus.SUCCESS
        self.emit(trace)

    def _on_node_error(self, name: str, event: dict) -> None:
        trace = self._active.pop(name, None)
        if trace is None:
            return
        trace.end_time = datetime.utcnow()
        trace.status = TraceStatus.ERROR
        trace.error_message = str(event.get("data", {}).get("error", "未知错误"))
        self.emit(trace)

    @staticmethod
    def _serialize(value: Any) -> str:
        if isinstance(value, dict):
            filtered = {
                k: v for k, v in value.items() if k not in {"callbacks", "config"}
            }
            if filtered:
                return json.dumps(filtered, ensure_ascii=False, default=str)[
                    :_MAX_SERIALIZE_LEN
                ]
        return str(value)[:_MAX_SERIALIZE_LEN]
