import React from 'react'
import { Row, Col, Card, Statistic, Table, Button } from 'antd'
import { PlusOutlined, RiseOutlined, BugOutlined, DatabaseOutlined } from '@ant-design/icons'

import './Dashboard.less'

const Dashboard: React.FC = () => {
  return (
    <div className="dashboard-container">
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <h1>安全概览</h1>
        </Col>

        {/* Statistics */}
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="漏洞总数"
              value={0}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="资产总数"
              value={0}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="关键漏洞"
              value={0}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#ff7a45' }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="风险评分"
              value={0}
              suffix="/ 100"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>

        {/* Recent Tasks */}
        <Col span={24}>
          <Card
            title="最近任务"
            extra={
              <Button type="primary" icon={<PlusOutlined />}>
                新建任务
              </Button>
            }
          >
            <Table
              columns={[
                { title: '任务名称', dataIndex: 'name', key: 'name' },
                { title: '类型', dataIndex: 'type', key: 'type' },
                { title: '状态', dataIndex: 'status', key: 'status' },
                { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
              ]}
              dataSource={[]}
              pagination={false}
            />
          </Card>
        </Col>

        {/* Risk Assets */}
        <Col span={24}>
          <Card title="风险资产排行">
            <Table
              columns={[
                { title: 'IP地址', dataIndex: 'ip', key: 'ip' },
                { title: '漏洞数', dataIndex: 'vulnerability_count', key: 'vulnerability_count' },
                { title: '严重程度', dataIndex: 'severity', key: 'severity' },
              ]}
              dataSource={[]}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
