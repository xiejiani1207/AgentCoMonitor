"""LangGraph 适配器——通过 callbacks 机制零侵入采集 Trace 数据。"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from agent_monitor.adapters.base import MonitoringAdapter
from agent_monitor.core.models import TraceRecord, TraceStatus


class LangGraphCallback(BaseCallbackHandler, MonitoringAdapter):
    """LangGraph 监控钩子。

    通过 LangGraph 原生的 config["callbacks"] 机制注入，Demo 端无需 import agent_monitor。

    用法:
        monitor = LangGraphCallback(on_trace=my_handler)
        graph.invoke(input, config={"callbacks": [monitor]})
    """

    def __init__(self, *args, **kwargs):
        MonitoringAdapter.__init__(self, *args, **kwargs)
        # 追踪当前活跃的 traces: chain_run_id → TraceRecord
        self._active: dict[str, TraceRecord] = {}
        # task_id 由外部注入或在第一个 chain start 时生成
        self._task_id: Optional[str] = None

    # ---- MonitoringAdapter 接口实现 ----

    def get_framework_name(self) -> str:
        return "langgraph"

    # ---- LangChain Callbacks ----

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        trace = TraceRecord(
            trace_id=str(run_id),
            task_id=self._task_id or str(run_id),
            agent_name=self._extract_agent_name(serialized, metadata),
            agent_role=metadata.get("agent_role", "") if metadata else "",
            input_prompt=self._serialize_inputs(inputs),
            output_content="",
            start_time=datetime.utcnow(),
            parent_trace_id=str(parent_run_id) if parent_run_id else None,
        )
        self._active[str(run_id)] = trace
        if self._task_id is None:
            self._task_id = trace.task_id

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        trace = self._active.pop(str(run_id), None)
        if trace is None:
            return

        trace.end_time = datetime.utcnow()
        trace.output_content = self._serialize_outputs(outputs)
        if trace.start_time:
            trace.duration_ms = int(
                (trace.end_time - trace.start_time).total_seconds() * 1000
            )
        trace.status = TraceStatus.SUCCESS

        self.emit(trace)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        trace = self._active.pop(str(run_id), None)
        if trace is None:
            return

        trace.end_time = datetime.utcnow()
        trace.status = TraceStatus.ERROR
        trace.error_message = str(error)

        self.emit(trace)

    def on_llm_end(self, response, *, run_id: UUID, **kwargs: Any) -> None:
        trace = self._active.get(str(run_id))
        if trace and hasattr(response, "llm_output"):
            usage = response.llm_output.get("token_usage", {})
            trace.token_used = usage.get("total_tokens", 0)

    # ---- 内部方法 ----

    def _extract_agent_name(
        self, serialized: dict[str, Any], metadata: Optional[dict[str, Any]]
    ) -> str:
        if metadata and "agent_name" in metadata:
            return metadata["agent_name"]
        return serialized.get("name", serialized.get("id", "unknown"))

    def _serialize_inputs(self, inputs: dict[str, Any]) -> str:
        # LangGraph 的 inputs 通常包含 state dict，转换为可读字符串
        if isinstance(inputs, dict):
            # 去掉内部键，只保留有意义的内容
            skip_keys = {"__start__", "callbacks", "config"}
            filtered = {k: v for k, v in inputs.items() if k not in skip_keys}
            if filtered:
                import json

                return json.dumps(filtered, ensure_ascii=False, default=str)
        return str(inputs)

    def _serialize_outputs(self, outputs: dict[str, Any]) -> str:
        if isinstance(outputs, dict):
            import json

            return json.dumps(outputs, ensure_ascii=False, default=str)
        return str(outputs)

    @property
    def task_id(self) -> Optional[str]:
        return self._task_id
