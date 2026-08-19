import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { Layout, Menu } from "antd";
import {
  DashboardOutlined,
  ApartmentOutlined,
  FileSearchOutlined,
  AlertOutlined,
  RobotOutlined,
} from "@ant-design/icons";
import Overview from "./pages/Overview";
import Topology from "./pages/Topology";
import TaskDetail from "./pages/TaskDetail";
import Alerts from "./pages/Alerts";
import Chat from "./pages/Chat";

const { Header, Content } = Layout;

const navItems = [
  { key: "/", icon: <DashboardOutlined />, label: <Link to="/">概览总览</Link> },
  { key: "/topology", icon: <ApartmentOutlined />, label: <Link to="/topology">链路追踪</Link> },
  { key: "/alerts", icon: <AlertOutlined />, label: <Link to="/alerts">异常告警</Link> },
  { key: "/chat", icon: <RobotOutlined />, label: <Link to="/chat">智能投顾</Link> },
];

function AppLayout() {
  const location = useLocation();
  const isTaskDetail = location.pathname.startsWith("/task/");

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center", padding: "0 24px" }}>
        <div style={{ color: "#fff", fontSize: 18, fontWeight: 600, marginRight: 32, whiteSpace: "nowrap" }}>
          AgentCoMonitor
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={isTaskDetail ? [] : [location.pathname]}
          items={navItems}
          style={{ flex: 1, minWidth: 0 }}
        />
      </Header>
      <Content style={{ background: "#f5f5f5" }}>
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/topology" element={<Topology />} />
          <Route path="/task/:taskId" element={<TaskDetail />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </Content>
    </Layout>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}
