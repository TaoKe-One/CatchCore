/**
 * Tool Results Viewer Component
 * Displays scan results from integrated security tools
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tabs,
  Tag,
  Button,
  Space,
  Statistic,
  Row,
  Col,
  Empty,
  Loading,
  message,
} from 'antd';
import {
  DownloadOutlined,
  ReloadOutlined,
  BugOutlined,
  SafetyOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import axios from 'axios';

interface ToolResult {
  id: number;
  task_id: number;
  tool: string;
  data: any;
  created_at: string;
}

interface TaskStatistics {
  task_id: number;
  task_name: string;
  task_status: string;
  tools_executed: string[];
  tools_count: number;
  total_ports: number;
  total_vulnerabilities: number;
  total_directories: number;
  total_findings: number;
  severity_distribution: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
}

interface ToolResultsData {
  task_id: number;
  task_name: string;
  task_status: string;
  results: ToolResult[];
  statistics: TaskStatistics;
  total_results: number;
}

interface Props {
  taskId: number;
  onRefresh?: () => void;
}

const ToolResultsViewer: React.FC<Props> = ({ taskId, onRefresh }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ToolResultsData | null>(null);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch tool results
  const fetchResults = async () => {
    setLoading(true);
    try {
      const response = await axios.get(
        `/api/v1/tools/task/${taskId}/results`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.data.code === 0) {
        setData(response.data.data);
        message.success('Tool results loaded');
      } else {
        message.error(response.data.message);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Failed to load tool results');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResults();
  }, [taskId]);

  const getSeverityColor = (severity: string) => {
    const colorMap: { [key: string]: string } = {
      critical: 'red',
      high: 'orange',
      medium: 'gold',
      low: 'blue',
      info: 'cyan',
    };
    return colorMap[severity?.toLowerCase()] || 'default';
  };

  const getToolIcon = (toolName: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      fscan: <DatabaseOutlined />,
      nuclei: <BugOutlined />,
      afrog: <SafetyOutlined />,
      dddd: <SafetyOutlined />,
      dirsearch: <DatabaseOutlined />,
    };
    return iconMap[toolName?.toLowerCase()] || <DatabaseOutlined />;
  };

  const renderOverviewTab = () => {
    if (!data?.statistics) {
      return <Empty description="No statistics available" />;
    }

    const stats = data.statistics;

    return (
      <div>
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Tools Executed"
                value={stats.tools_count}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Findings"
                value={stats.total_findings}
                suffix={`Port${stats.total_ports > 0 ? 's' : ''} + Vuln${stats.total_vulnerabilities > 0 ? 's' : ''}`}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Vulnerabilities"
                value={stats.total_vulnerabilities}
                prefix={<BugOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Open Ports"
                value={stats.total_ports}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>

        <Card title="Severity Distribution">
          <Row gutter={[16, 16]}>
            {Object.entries(stats.severity_distribution).map(([severity, count]) => (
              <Col key={severity} xs={12} sm={8} md={4}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                    {count}
                  </div>
                  <Tag color={getSeverityColor(severity)}>
                    {severity.toUpperCase()}
                  </Tag>
                </div>
              </Col>
            ))}
          </Row>
        </Card>

        <Card title="Tools Used" style={{ marginTop: '16px' }}>
          <Space wrap>
            {stats.tools_executed.map((tool) => (
              <Tag key={tool} color="blue">
                {getToolIcon(tool)} {tool.toUpperCase()}
              </Tag>
            ))}
          </Space>
        </Card>
      </div>
    );
  };

  const renderFscanResults = (result: ToolResult) => {
    const results = result.data.results || [];
    const columns = [
      {
        title: 'IP Address',
        dataIndex: 'ip',
        key: 'ip',
      },
      {
        title: 'Port',
        dataIndex: 'port',
        key: 'port',
      },
      {
        title: 'Service',
        dataIndex: 'service',
        key: 'service',
      },
      {
        title: 'Version',
        dataIndex: 'version',
        key: 'version',
      },
    ];

    return (
      <Card
        title={`FScan Results - ${results.length} ports found`}
        extra={<Tag color="blue">Port Scan</Tag>}
      >
        <Table
          dataSource={results}
          columns={columns}
          rowKey={(record, index) => `${record.ip}-${record.port}-${index}`}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    );
  };

  const renderNucleiResults = (result: ToolResult) => {
    const results = result.data.results || [];
    const columns = [
      {
        title: 'Vulnerability',
        dataIndex: 'name',
        key: 'name',
        width: '40%',
      },
      {
        title: 'Severity',
        dataIndex: 'severity',
        key: 'severity',
        render: (severity: string) => (
          <Tag color={getSeverityColor(severity)}>
            {severity?.toUpperCase()}
          </Tag>
        ),
      },
      {
        title: 'Matched At',
        dataIndex: 'matched_at',
        key: 'matched_at',
        width: '40%',
      },
    ];

    return (
      <Card
        title={`Nuclei Results - ${results.length} vulnerabilities found`}
        extra={<Tag color="red">Vulnerability Scan</Tag>}
      >
        <Table
          dataSource={results}
          columns={columns}
          rowKey={(record, index) => `${record.id}-${index}`}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    );
  };

  const renderAfrogResults = (result: ToolResult) => {
    const results = result.data.results || [];
    const columns = [
      {
        title: 'Vulnerability',
        dataIndex: 'vulnerability',
        key: 'vulnerability',
        width: '40%',
      },
      {
        title: 'Severity',
        dataIndex: 'severity',
        key: 'severity',
        render: (severity: string) => (
          <Tag color={getSeverityColor(severity)}>
            {severity?.toUpperCase()}
          </Tag>
        ),
      },
      {
        title: 'Target',
        dataIndex: 'target',
        key: 'target',
        width: '40%',
      },
    ];

    return (
      <Card
        title={`Afrog Results - ${results.length} vulnerabilities found`}
        extra={<Tag color="red">PoC Scan</Tag>}
      >
        <Table
          dataSource={results}
          columns={columns}
          rowKey={(record, index) => `${record.vulnerability}-${index}`}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    );
  };

  const renderDirsearchResults = (result: ToolResult) => {
    const results = result.data.results || [];
    const columns = [
      {
        title: 'Path',
        dataIndex: 'path',
        key: 'path',
        width: '50%',
      },
      {
        title: 'HTTP Status',
        dataIndex: 'status',
        key: 'status',
        render: (status: number) => {
          let color = 'green';
          if (status >= 400) color = 'red';
          else if (status >= 300) color = 'blue';
          return <Tag color={color}>{status}</Tag>;
        },
      },
    ];

    return (
      <Card
        title={`DirSearch Results - ${results.length} directories found`}
        extra={<Tag color="orange">Directory Enum</Tag>}
      >
        <Table
          dataSource={results}
          columns={columns}
          rowKey={(record, index) => `${record.path}-${index}`}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    );
  };

  const renderToolResults = (result: ToolResult) => {
    const tool = result.tool.toLowerCase();

    switch (tool) {
      case 'fscan':
        return renderFscanResults(result);
      case 'nuclei':
        return renderNucleiResults(result);
      case 'afrog':
        return renderAfrogResults(result);
      case 'dirsearch':
        return renderDirsearchResults(result);
      default:
        return (
          <Card title={`${tool.toUpperCase()} Results`}>
            <pre>{JSON.stringify(result.data, null, 2)}</pre>
          </Card>
        );
    }
  };

  const renderResultsTab = () => {
    if (!data?.results || data.results.length === 0) {
      return <Empty description="No tool results available" />;
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {data.results.map((result) => (
          <div key={result.id}>{renderToolResults(result)}</div>
        ))}
      </div>
    );
  };

  const renderRawDataTab = () => {
    if (!data?.results || data.results.length === 0) {
      return <Empty description="No tool results available" />;
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {data.results.map((result) => (
          <Card
            key={result.id}
            title={`${result.tool.toUpperCase()} - Raw JSON`}
            extra={
              <Button
                type="text"
                icon={<DownloadOutlined />}
                onClick={() => {
                  const element = document.createElement('a');
                  element.href = `data:text/json;charset=utf-8,${encodeURIComponent(
                    JSON.stringify(result.data, null, 2)
                  )}`;
                  element.download = `${result.tool}_result.json`;
                  document.body.appendChild(element);
                  element.click();
                  document.body.removeChild(element);
                }}
              >
                Download
              </Button>
            }
          >
            <pre style={{ maxHeight: '400px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '12px' }}>
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </Card>
        ))}
      </div>
    );
  };

  if (loading) {
    return <Loading />;
  }

  return (
    <div>
      <Card
        title={`Tool Scan Results for Task: ${data?.task_name}`}
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={fetchResults}>
              Refresh
            </Button>
            {onRefresh && (
              <Button type="primary" onClick={onRefresh}>
                Back to Task
              </Button>
            )}
          </Space>
        }
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'overview',
              label: '📊 Overview',
              children: renderOverviewTab(),
            },
            {
              key: 'results',
              label: `🔍 Results (${data?.results?.length || 0})`,
              children: renderResultsTab(),
            },
            {
              key: 'raw',
              label: '📄 Raw Data',
              children: renderRawDataTab(),
            },
          ]}
        />
      </Card>
    </div>
  );
};

export default ToolResultsViewer;
