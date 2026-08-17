import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, Collapse, Descriptions, Spin, Table, Tag, Timeline, Typography } from "antd";
import { api, QualityScore, Trace } from "../api/client";

const { Title, Paragraph, Text } = Typography;

const statusColor: Record<string, string> = {
  success: "green",
  error: "red",
  pending: "default",
  timeout: "red",
  retry: "orange",
};

function QualityPanel({ traceId }: { traceId: string }) {
  const [score, setScore] = useState<QualityScore | null>(null);
  useEffect(() => {
    api.quality(traceId).then(setScore).catch(() => setScore(null));
  }, [traceId]);

  if (!score) return <Text type="secondary">暂无质量评分</Text>;

  const dims = [
    { key: "accuracy", label: "准确性" },
    { key: "completeness", label: "完整性" },
    { key: "relevance", label: "相关性" },
    { key: "compliance", label: "合规性" },
    { key: "timeliness", label: "时效性" },
  ];

  // 简易雷达图占位
  return (
    <div>
      <Text strong>
        综合分: {score.overall_score} ({score.eval_method})
      </Text>
      <table style={{ width: "100%", marginTop: 8, borderCollapse: "collapse" }}>
        <tbody>
          {dims.map((d) => {
            const val = score[d.key as keyof QualityScore] as number | null;
            const color = val != null ? (val < 60 ? "#ff4d4f" : val < 80 ? "#faad14" : "#52c41a") : "#d9d9d9";
            return (
              <tr key={d.key}>
                <td style={{ padding: "4px 8px", width: 80 }}>{d.label}</td>
                <td style={{ padding: "4px 8px" }}>
                  <div style={{ background: "#f0f0f0", height: 12, borderRadius: 6, overflow: "hidden" }}>
                    <div
                      style={{
                        width: `${val ?? 0}%`,
                        height: "100%",
                        background: color,
                        borderRadius: 6,
                        transition: "width 0.3s",
                      }}
                    />
                  </div>
                </td>
                <td style={{ padding: "4px 8px", width: 60, textAlign: "right" }}>
                  {val != null ? val : "-"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function TaskDetail() {
  const { taskId } = useParams<{ taskId: string }>();
  const [traces, setTraces] = useState<Trace[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) return;
    api.traces(taskId).then((ts) => { setTraces(ts); setLoading(false); }).catch(() => setLoading(false));
  }, [taskId]);

  // 构建时间线：按 start_time 排序
  const sorted = [...traces].sort(
    (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  );

  if (loading) return <Spin style={{ margin: "40px auto", display: "block" }} />;

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>任务详情: {taskId}</Title>

      <Timeline
        items={sorted.map((t) => ({
          color: statusColor[t.status] === "green" ? "green" : statusColor[t.status] === "red" ? "red" : "blue",
          children: (
            <Card
              size="small"
              title={
                <span>
                  <Tag color={statusColor[t.status]}>{t.status}</Tag>
                  {t.agent_name}
                  <Text type="secondary" style={{ marginLeft: 12 }}>
                    {t.agent_role} | {t.duration_ms != null ? `${t.duration_ms}ms` : "-"} | token: {t.token_used ?? "-"}
                  </Text>
                </span>
              }
            >
              <Collapse
                size="small"
                ghost
                items={[
                  {
                    key: "input",
                    label: "输入",
                    children: <Paragraph style={{ whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto", background: "#fafafa", padding: 8, borderRadius: 4 }}>
                      {t.input_prompt || "无"}
                    </Paragraph>,
                  },
                  {
                    key: "output",
                    label: "输出",
                    children: <Paragraph style={{ whiteSpace: "pre-wrap", maxHeight: 300, overflow: "auto", background: "#fafafa", padding: 8, borderRadius: 4 }}>
                      {t.output_content || "无"}
                    </Paragraph>,
                  },
                  {
                    key: "quality",
                    label: "质量评分",
                    children: <QualityPanel traceId={t.trace_id} />,
                  },
                ]}
              />
            </Card>
          ),
        }))}
      />
    </div>
  );
}
