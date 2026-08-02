import { useEffect, useState } from "react";
import { Card, Select, Space, Table, Tag, Typography } from "antd";
import { api, AnomalyEvent } from "../api/client";
import { useWebSocket } from "../hooks/useWebSocket";

const { Title } = Typography;

const severityColor: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "blue",
};

export default function Alerts() {
  const [alerts, setAlerts] = useState<AnomalyEvent[]>([]);
  const [filter, setFilter] = useState<string>("all");

  const load = () => {
    api.anomalies().then(setAlerts).catch(console.error);
  };

  useEffect(() => { load(); }, []);

  // WebSocket 实时刷新
  useWebSocket((msg) => {
    if (msg.event === "trace_updated") load();
  });

  const filtered = filter === "all" ? alerts : alerts.filter((a) => a.severity === filter);

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>异常告警</Title>

      <Space style={{ marginBottom: 16 }}>
        <Select
          value={filter}
          onChange={setFilter}
          style={{ width: 120 }}
          options={[
            { value: "all", label: "全部" },
            { value: "high", label: "高危" },
            { value: "medium", label: "中危" },
            { value: "low", label: "低危" },
          ]}
        />
      </Space>

      <Table
        dataSource={filtered}
        rowKey="id"
        columns={[
          {
            title: "级别",
            dataIndex: "severity",
            width: 80,
            render: (s: string) => <Tag color={severityColor[s]}>{s}</Tag>,
          },
          { title: "类型", dataIndex: "anomaly_type", width: 140 },
          { title: "层级", dataIndex: "layer", width: 100 },
          { title: "描述", dataIndex: "description", ellipsis: true },
          {
            title: "建议",
            dataIndex: "suggestion",
            ellipsis: true,
            render: (s: string | null) => s || "-",
          },
          {
            title: "时间",
            dataIndex: "created_at",
            width: 180,
            render: (d: string) => new Date(d).toLocaleString("zh-CN"),
          },
        ]}
      />
    </div>
  );
}
