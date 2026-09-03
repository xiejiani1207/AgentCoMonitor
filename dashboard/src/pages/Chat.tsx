import { useEffect, useState } from "react";
import { Button, Card, Collapse, Input, Space, Spin, Switch, Tag, Typography } from "antd";
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  ClearOutlined,
  RobotOutlined,
  SendOutlined,
  UserOutlined,
  WarningOutlined,
} from "@ant-design/icons";
import { chat, ChatResponse, ViolationItem } from "../api/client";

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
  value_investor: "价值投资",
  trend_trader: "趋势交易",
  decision_maker: "综合决策",
  compliance_checker: "合规",
};

const AGENT_ORDER = [
  "data_collector",
  "technical_analyst",
  "fundamental_analyst",
  "risk_assessor",
  "value_investor",
  "trend_trader",
  "decision_maker",
];

const REPORT_SECTIONS = [
  { key: "technical_report", label: "技术面分析" },
  { key: "fundamental_report", label: "基本面分析" },
  { key: "risk_report", label: "风控评估" },
  { key: "decision", label: "综合决策" },
  { key: "compliance_result", label: "合规审查" },
] as const;

const RECOMMENDATION_LABELS: Record<string, string> = {
  adopted: "采纳",
  alternative: "备选",
  archived: "存档",
};

interface Turn {
  query: string;
  result: ChatResponse;
}

function highlightViolations(text: string, violations: ViolationItem[]) {
  if (!violations.length) return text;
  const offending = new Set(violations.map((v) => v.sentence.trim()));
  const parts = text.split(/([。！？!?])/);
  return (
    <>
      {parts.map((part, i) =>
        offending.has(part.trim()) ? (
          <span key={i} style={{ background: "#ffccc7", color: "#cf1322", fontWeight: 600 }}>
            {part}
          </span>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

function ReportCard({ result }: { result: ChatResponse }) {
  return (
    <>
      {result.demo_mode && (
        <Card style={{ marginTop: 12, background: "#fff7e6" }}>
          <Tag color="orange" icon={<WarningOutlined />}>演示模式</Tag>
          <Text>本次已人为注入破绽（合规违规 + 超时），用于演示反馈闭环</Text>
        </Card>
      )}
      <Card
        title={`${result.report.stock_name ?? ""} (${result.report.stock_code ?? ""})`}
        style={{ marginTop: 12 }}
      >
        <Paragraph style={{ whiteSpace: "pre-wrap", fontSize: 15, marginBottom: 0 }}>
          {result.report.final_output || "（无最终输出）"}
        </Paragraph>
      </Card>
      <Card title="分析报告" style={{ marginTop: 12 }}>
        <Collapse
          size="small"
          items={REPORT_SECTIONS.map((s) => ({
            key: s.key,
            label: s.label,
            children:
              s.key === "decision" ? (
                <div>
                  <Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                    {highlightViolations(result.report.decision, result.report.violations)}
                  </Paragraph>
                  {result.report.violations.length > 0 && (
                    <Space wrap size={4} style={{ marginTop: 8 }}>
                      {result.report.violations.map((v, i) => (
                        <Tag key={i} color="red">命中「{v.words.join("、")}」</Tag>
                      ))}
                    </Space>
                  )}
                </div>
              ) : (
                <Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                  {result.report[s.key] || "（无）"}
                </Paragraph>
              ),
          }))}
        />
      </Card>
      <Card title="监控质检" style={{ marginTop: 12 }}>
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
        {result.feedback.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary">反馈闭环：</Text>
            <Space wrap size={4} style={{ marginTop: 8 }}>
              <Tag color="purple">已生成 {result.feedback.length} 条指令回灌 demo</Tag>
              {result.feedback.map((f, i) => (
                <Tag key={i} color="purple">
                  {AGENT_LABELS[f.target_agent] ?? f.target_agent} / {f.dimension}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </Card>

      {result.ranking.length > 0 && (
        <Card title="结果筛选优化" style={{ marginTop: 12 }}>
          <Space wrap size={4}>
            {result.ranking.map((r) => (
              <Tag
                key={r.rank}
                color={
                  r.recommendation === "adopted"
                    ? "green"
                    : r.recommendation === "alternative"
                      ? "blue"
                      : "default"
                }
              >
                #{r.rank} {RECOMMENDATION_LABELS[r.recommendation]}{" "}
                {AGENT_LABELS[r.agent_name] ?? r.agent_name}（{r.quality_score}）
              </Tag>
            ))}
          </Space>
        </Card>
      )}
    </>
  );
}

export default function Chat() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pendingQuery, setPendingQuery] = useState<string | null>(null);
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
    setQuery("");
    setLoading(true);
    setError(null);
    setDoneAgents([]);
    setPendingQuery(text);
    const history = turns.map((t) => t.query);
    try {
      const result = await chat(text, demoMode, history);
      setTurns((prev) => [...prev, { query: text, result }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
      setPendingQuery(null);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 880, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <Title level={3} style={{ marginBottom: 0 }}>
            <RobotOutlined /> 智能投顾助手
          </Title>
          <Text type="secondary">
            多轮对话 · 6 个 Agent 协同分析 · 监控平台实时质检
          </Text>
        </div>
        {turns.length > 0 && (
          <Button icon={<ClearOutlined />} onClick={() => setTurns([])}>清空对话</Button>
        )}
      </div>

      <Card style={{ marginTop: 16 }}>
        <Space style={{ marginBottom: 12 }}>
          <Switch checked={demoMode} onChange={setDemoMode} />
          <Text type="secondary">演示模式：注入合规违规 + 超时异常</Text>
        </Space>
        <Input.TextArea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="例如：分析 600519 贵州茅台（可追问，如「那风险大不大？」）"
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

      {turns.map((t, i) => (
        <div key={i}>
          <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
            <Card size="small" style={{ maxWidth: "70%", background: "#e6f4ff" }}>
              <Space>
                <UserOutlined />
                <Text strong>{t.query}</Text>
              </Space>
            </Card>
          </div>
          <ReportCard result={t.result} />
        </div>
      ))}

      {pendingQuery && (
        <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
          <Card size="small" style={{ maxWidth: "70%", background: "#e6f4ff" }}>
            <Space>
              <UserOutlined />
              <Text strong>{pendingQuery}</Text>
            </Space>
          </Card>
        </div>
      )}

      {loading && (
        <Card style={{ marginTop: 12 }}>
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
    </div>
  );
}
