import { useEffect, useRef, useState } from "react";
import { Card, Select, Space, Tag, Typography } from "antd";
import { Graph } from "@antv/g6";
import { api, Trace } from "../api/client";
import { useWebSocket } from "../hooks/useWebSocket";

const { Title, Text } = Typography;

const statusColor: Record<string, string> = {
  success: "#52c41a",
  error: "#ff4d4f",
  pending: "#d9d9d9",
  retry: "#faad14",
  timeout: "#ff4d4f",
};

export default function Topology() {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<InstanceType<typeof Graph> | null>(null);
  const [taskId, setTaskId] = useState<string>("");
  const [nodes, setNodes] = useState<Array<{ id: string; label: string; status: string }>>([]);
  const [edges, setEdges] = useState<Array<{ source: string; target: string }>>([]);

  const [tasks, setTasks] = useState<Array<{ task_id: string; title: string }>>([]);

  // 加载任务列表
  useEffect(() => {
    api.tasks(20).then((ts) => setTasks(ts.map((t) => ({ task_id: t.task_id, title: t.title || t.task_id })))).catch(console.error);
  }, []);

  // 选中任务后加载 Traces 并构建图
  useEffect(() => {
    if (!taskId) return;
    api.traces(taskId).then((traces) => {
      const ns = traces.map((t) => ({
        id: t.trace_id,
        label: t.agent_name,
        status: t.status,
      }));
      const es: Array<{ source: string; target: string }> = [];
      for (const t of traces) {
        if (t.parent_trace_id) {
          es.push({ source: t.parent_trace_id, target: t.trace_id });
        }
      }
      setNodes(ns);
      setEdges(es);
    }).catch(console.error);
  }, [taskId]);

  // 渲染 G6 图
  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    if (graphRef.current) {
      graphRef.current.destroy();
    }

    // G6 v5 graph
    const graph = new Graph({
      container: containerRef.current,
      width: containerRef.current.clientWidth,
      height: 500,
      data: {
        nodes: nodes.map((n) => ({
          id: n.id,
          data: { label: n.label, status: n.status },
          style: { fill: statusColor[n.status] || "#d9d9d9" },
        })),
        edges: edges.map((e) => ({
          source: e.source,
          target: e.target,
          style: { stroke: "#bbb", lineWidth: 2, endArrow: true },
        })),
      },
      node: {
        style: { size: 40, labelText: (d: any) => d.data?.label || "", labelFontSize: 12 },
      },
      layout: { type: "dagre", rankdir: "LR", nodesep: 30, ranksep: 100 },
      behaviors: ["drag-canvas", "zoom-canvas", "drag-element"],
      autoFit: "view",
    });

    graph.render();
    graphRef.current = graph;

    return () => {
      graph.destroy();
      graphRef.current = null;
    };
  }, [nodes, edges]);

  // WebSocket 实时更新节点状态
  useWebSocket((msg) => {
    if (msg.event === "trace_updated" && graphRef.current) {
      const traceId = msg.data.trace_id as string;
      setNodes((prev) =>
        prev.map((n) => (n.id === traceId ? { ...n, status: "success" } : n))
      );
    }
  });

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>链路追踪</Title>

      <Space style={{ marginBottom: 16 }}>
        <Text>选择任务：</Text>
        <Select
          style={{ width: 300 }}
          placeholder="选择要查看的任务"
          value={taskId || undefined}
          onChange={(v) => setTaskId(v)}
          options={tasks.map((t) => ({ value: t.task_id, label: t.title }))}
        />
      </Space>

      {nodes.length > 0 && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            {nodes.map((n) => (
              <Tag key={n.id} color={statusColor[n.status]}>
                {n.label}: {n.status}
              </Tag>
            ))}
          </Space>
        </Card>
      )}

      <Card>
        <div ref={containerRef} style={{ width: "100%", minHeight: 500 }} />
      </Card>
    </div>
  );
}
