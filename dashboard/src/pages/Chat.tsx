import { useState } from "react";
import { Button, Card, Collapse, Input, Space, Spin, Tag, Typography } from "antd";
import { RobotOutlined, SendOutlined } from "@ant-design/icons";
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

  const send = async (q?: string) => {
    const text = (q ?? query).trim();
    if (!text || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await chat(text));
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
        <Card style={{ marginTop: 16, textAlign: "center" }}>
          <Spin tip="分析中…（6 个 Agent 协同，约 15 秒）">
            <div style={{ minHeight: 80 }} />
          </Spin>
        </Card>
      )}

      {error && (
        <Card style={{ marginTop: 16 }}>
          <Text type="danger">{error}</Text>
        </Card>
      )}

      {result && (
        <>
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
