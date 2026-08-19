import { useEffect, useState } from "react";
import { Button, Card, Collapse, Input, Space, Spin, Switch, Tag, Typography } from "antd";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  RobotOutlined,
  SendOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { chat, ChatResponse } from "../api/client";

const { Title, Text, Paragraph } = Typography;

const EXAMPLES = [
  "分析 600519 贵州茅台",
  "分析 300750 宁德时代",
  "看下 688981 中芯国际",
];

const AGENT_LABELS: Record<string, string> = {
  data_collector: "数据采集",
  technical_analyst: "技术面",
  fundamental_analyst: "基本面",
  risk_assessor: "风控",
  decision_maker: "决策",
  compliance_checker: "合规",
};

const AGENT_ORDER = [
  "data_collector",
  "technical_analyst",
  "fundamental_analyst",
  "risk_assessor",
  "decision_maker",
  "compliance_checker",
];

const REPORT_SECTIONS = [
  { key: "technical_report", label: "技术面分析" },
  { key: "fundamental_report", label: "基本面分析" },
  { key: "risk_report", label: "风控评估" },
  { key: "decision", label: "综合决策" },
  { key: "compliance_result", label: "合规审查" },
] as const;

export default function Chat() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [doneAgents, setDoneAgents] = useState<string[]>([]);
  const [demoMode, setDemoMode] = useState(false);

  // 连接投顾服务的进度 WebSocket，实时点亮步骤条
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/advisory/ws`);
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.event === "agent_finished") {
          const name = msg.data?.agent_name as string | undefined;
          if (name) {
            setDoneAgents((prev) => (prev.includes(name) ? prev : [...prev, name]));
          }
        }
      } catch {
        // 忽略无法解析的消息
      }
    };
    return () => ws.close();
  }, []);

  const send = async (q?: string) => {
    const text = (q ?? query).trim();
    if (!text || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setDoneAgents([]);
    try {
      setResult(await chat(text, demoMode));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 880, margin: "0 auto" }}>
      <Title level={3}>
        <RobotOutlined /> 智能投顾助手
      </Title>
      <Text type="secondary">
        输入股票代码或名称，6 个 Agent 协同分析，并由监控平台实时质检
      </Text>

      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 12 }}>
          <Switch checked={demoMode} onChange={setDemoMode} />
          <Text type="secondary">演示模式：注入合规违规 + 超时异常</Text>
        </Space>
        <Input.TextArea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：分析 600519 贵州茅台"
          autoSize={{ minRows: 2, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
        />
        <div
          style={{
            marginTop: 12,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <Space wrap size={4}>
            {EXAMPLES.map((ex) => (
              <Tag
                key={ex}
                style={{ cursor: "pointer" }}
                onClick={() => {
                  setQuery(ex);
                  send(ex);
                }}
              >
                {ex}
              </Tag>
            ))}
          </Space>
          <Button type="primary" icon={<SendOutlined />} loading={loading} onClick={() => send()}>
            发送
          </Button>
        </div>
      </Card>

      {loading && (
        <Card style={{ marginTop: 16 }}>
          <Spin tip="分析中…">
            <div style={{ minHeight: 32 }} />
          </Spin>
          <Space wrap size={4} style={{ marginTop: 12 }}>
            {AGENT_ORDER.map((name) => {
              const done = doneAgents.includes(name);
              return (
                <Tag
                  key={name}
                  color={done ? "green" : "default"}
                  icon={done ? <CheckCircleOutlined /> : <ClockCircleOutlined />}
                >
                  {AGENT_LABELS[name]}
                </Tag>
              );
            })}
          </Space>
        </Card>
      )}

      {error && (
        <Card style={{ marginTop: 16 }}>
          <Text type="danger">{error}</Text>
        </Card>
      )}

      {result && (
        <>
          {result.demo_mode && (
            <Card style={{ marginTop: 16, background: "#fff7e6" }}>
              <Tag color="orange" icon={<WarningOutlined />}>演示模式</Tag>
              <Text>本次已人为注入破绽（合规违规 + 超时），用于演示反馈闭环</Text>
            </Card>
          )}
          <Card
            title={`${result.report.stock_name ?? ""} (${result.report.stock_code ?? ""})`}
            style={{ marginTop: 16 }}
          >
            <Paragraph style={{ whiteSpace: "pre-wrap", fontSize: 15, marginBottom: 0 }}>
              {result.report.final_output || "（无最终输出）"}
            </Paragraph>
          </Card>

          <Card title="分析报告" style={{ marginTop: 16 }}>
            <Collapse
              size="small"
              items={REPORT_SECTIONS.map((s) => ({
                key: s.key,
                label: s.label,
                children: (
                  <Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                    {result.report[s.key] || "（无）"}
                  </Paragraph>
                ),
              }))}
            />
          </Card>

          <Card title="监控质检" style={{ marginTop: 16 }}>
            <Space wrap size={8}>
              <Tag color="blue">综合质量 {result.monitoring.avg_quality_score ?? "-"}</Tag>
              <Tag
                color={
                  result.monitoring.min_compliance != null && result.monitoring.min_compliance < 100
                    ? "red"
                    : "green"
                }
              >
                合规 {result.monitoring.min_compliance ?? "-"}
              </Tag>
              <Tag color={result.monitoring.anomaly_count > 0 ? "red" : "green"}>
                异常 {result.monitoring.anomaly_count}
              </Tag>
              <Tag>建议 {result.monitoring.suggestion_count}</Tag>
            </Space>
            <div style={{ marginTop: 12 }}>
              <Text type="secondary">各 Agent 质量分：</Text>
              <Space wrap size={4} style={{ marginTop: 8 }}>
                {result.monitoring.traces.map((t) => (
                  <Tag key={t.agent_name} color={t.status === "success" ? "default" : "red"}>
                    {AGENT_LABELS[t.agent_name] ?? t.agent_name}: {t.overall_score ?? "-"}
                  </Tag>
                ))}
              </Space>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
