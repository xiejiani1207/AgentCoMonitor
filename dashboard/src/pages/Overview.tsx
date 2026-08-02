import { useEffect, useState } from "react";
import { Card, Col, Row, Statistic, Table, Tag, Typography } from "antd";
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import { api, AnomalyEvent, Task } from "../api/client";
import { useNavigate } from "react-router-dom";

const { Title } = Typography;

const statusIcon: Record<string, React.ReactNode> = {
  completed: <CheckCircleOutlined style={{ color: "#52c41a" }} />,
  failed: <CloseCircleOutlined style={{ color: "#ff4d4f" }} />,
  running: <SyncOutlined spin style={{ color: "#1677ff" }} />,
  pending: <SyncOutlined style={{ color: "#d9d9d9" }} />,
};

const severityColor: Record<string, string> = {
  high: "red",
  medium: "orange",
  low: "blue",
};

export default function Overview() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [alerts, setAlerts] = useState<AnomalyEvent[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    api.tasks(20).then(setTasks).catch(console.error);
    api.anomalies().then(setAlerts).catch(console.error);
  }, []);

  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const failedCount = tasks.filter((t) => t.status === "failed").length;
  const highAlerts = alerts.filter((a) => a.severity === "high").length;

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>概览总览</Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="总任务数" value={tasks.length} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={completedCount}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="失败"
              value={failedCount}
              valueStyle={{ color: failedCount > 0 ? "#ff4d4f" : undefined }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="高危告警"
              value={highAlerts}
              valueStyle={{ color: highAlerts > 0 ? "#ff4d4f" : undefined }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近任务" style={{ marginBottom: 24 }}>
        <Table
          dataSource={tasks.slice(0, 10)}
          rowKey="task_id"
          size="small"
          pagination={false}
          onRow={(r) => ({ onClick: () => navigate(`/task/${r.task_id}`), style: { cursor: "pointer" } })}
          columns={[
            { title: "任务ID", dataIndex: "task_id", ellipsis: true, width: 240 },
            {
              title: "状态",
              dataIndex: "status",
              width: 100,
              render: (s: string) => <Tag icon={statusIcon[s]}>{s}</Tag>,
            },
            {
              title: "创建时间",
              dataIndex: "created_at",
              width: 200,
              render: (d: string) => new Date(d).toLocaleString("zh-CN"),
            },
          ]}
        />
      </Card>

      <Card title="最近告警">
        <Table
          dataSource={alerts.slice(0, 10)}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            {
              title: "级别",
              dataIndex: "severity",
              width: 80,
              render: (s: string) => <Tag color={severityColor[s]}>{s}</Tag>,
            },
            { title: "类型", dataIndex: "anomaly_type", width: 120 },
            { title: "描述", dataIndex: "description", ellipsis: true },
            {
              title: "时间",
              dataIndex: "created_at",
              width: 180,
              render: (d: string) => new Date(d).toLocaleString("zh-CN"),
            },
          ]}
        />
      </Card>
    </div>
  );
}
