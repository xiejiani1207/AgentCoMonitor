import { useEffect, useState } from "react";
import {
  Button,
  Card,
  Input,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { api, SensitiveWord } from "../api/client";

const { Title, Text } = Typography;

const CATEGORIES = ["收益承诺", "风险误导", "绝对化用语", "未分类"];

export default function SensitiveWords() {
  const [words, setWords] = useState<SensitiveWord[]>([]);
  const [newWord, setNewWord] = useState("");
  const [newCategory, setNewCategory] = useState("未分类");
  const [loading, setLoading] = useState(false);

  const load = () => {
    api.sensitiveWords().then(setWords).catch(console.error);
  };

  useEffect(() => {
    load();
  }, []);

  const add = async () => {
    const w = newWord.trim();
    if (!w) return;
    setLoading(true);
    try {
      await api.addSensitiveWord(w, newCategory);
      message.success("已添加");
      setNewWord("");
      load();
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const remove = async (id: number) => {
    try {
      await api.deleteSensitiveWord(id);
      message.success("已删除");
      load();
    } catch (e) {
      message.error(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 880, margin: "0 auto" }}>
      <Title level={3}>敏感词库</Title>
      <Text type="secondary">合规检测的规则来源，输出命中即标红拦截</Text>

      <Card style={{ marginTop: 16 }}>
        <Space wrap>
          <Input
            placeholder="输入敏感词"
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            style={{ width: 200 }}
            onPressEnter={add}
          />
          <Select
            value={newCategory}
            onChange={setNewCategory}
            style={{ width: 140 }}
            options={CATEGORIES.map((c) => ({ value: c, label: c }))}
          />
          <Button type="primary" icon={<PlusOutlined />} loading={loading} onClick={add}>
            添加
          </Button>
        </Space>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Table
          dataSource={words}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: "敏感词", dataIndex: "word" },
            {
              title: "分类",
              dataIndex: "category",
              width: 140,
              render: (c: string) => <Tag>{c}</Tag>,
            },
            {
              title: "操作",
              width: 100,
              render: (_, r) => (
                <Popconfirm title="确认删除？" onConfirm={() => remove(r.id)}>
                  <Button danger size="small" type="link">
                    删除
                  </Button>
                </Popconfirm>
              ),
            },
          ]}
        />
      </Card>
    </div>
  );
}
