import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Card,
  Button,
  Spin,
  Progress,
  Tabs,
  Space,
  Tag,
  Row,
  Col,
  Empty,
  List,
  Divider,
  Statistic,
  Result,
  message,
} from 'antd'
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import apiService from '../../services/api'
import { useTaskProgress, TaskLog, TaskResult } from '../../hooks/useTaskProgress'
import './TaskDetail.css'

const TaskDetail: React.FC = () => {
  const { taskId: taskIdStr } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const taskId = parseInt(taskIdStr || '0', 10)

  const {
    isConnected,
    status,
    progress,
    logs,
    results,
    error,
    isCompleted,
    connect,
    disconnect,
    requestStatus,
    requestLogs,
  } = useTaskProgress(taskId, true)

  const [loading, setLoading] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)

  useEffect(() => {
    if (taskId) {
      requestStatus()
      requestLogs()
    }
  }, [taskId, requestStatus, requestLogs])

  const handleRefresh = async () => {
    setLoading(true)
    try {
      requestStatus()
      requestLogs()
    } catch (err) {
      message.error('Failed to refresh')
    } finally {
      setLoading(false)
    }
  }

  const handleTaskAction = async (action: string) => {
    try {
      switch (action) {
        case 'start':
          await apiService.startTask(taskId)
          message.success('Task started')
          break
        case 'pause':
          await apiService.pauseTask(taskId)
          message.success('Task paused')
          break
        case 'resume':
          await apiService.resumeTask(taskId)
          message.success('Task resumed')
          break
        case 'cancel':
          await apiService.cancelTask(taskId)
          message.success('Task cancelled')
          break
        default:
          break
      }
      handleRefresh()
    } catch (err) {
      message.error(`Action failed: ${action}`)
    }
  }

  const handleExportResults = () => {
    const dataStr = JSON.stringify(results, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `task-${taskId}-results.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const getStatusIcon = () => {
    if (!status) return null
    const iconProps = { style: { fontSize: '24px' } }

    switch (status.status) {
      case 'completed':
        return <CheckCircleOutlined {...iconProps} style={{ color: '#52c41a' }} />
      case 'failed':
        return <CloseCircleOutlined {...iconProps} style={{ color: '#f5222d' }} />
      case 'running':
        return <Spin size="large" />
      case 'paused':
        return <ExclamationCircleOutlined {...iconProps} style={{ color: '#faad14' }} />
      default:
        return <ExclamationCircleOutlined {...iconProps} style={{ color: '#8c8c8c' }} />
    }
  }

  const getStatusColor = () => {
    if (!status) return 'default'
    switch (status.status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      case 'running':
        return 'processing'
      case 'paused':
        return 'warning'
      default:
        return 'default'
    }
  }

  const logColors = {
    DEBUG: '#8c8c8c',
    INFO: '#1890ff',
    WARNING: '#faad14',
    ERROR: '#f5222d',
    CRITICAL: '#ff4d4f',
  }

  if (!status && !loading) {
    return (
      <div style={{ padding: '24px' }}>
        <Button
          type="link"
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/tasks')}
          style={{ marginBottom: '16px' }}
        >
          Back to Tasks
        </Button>
        <Empty
          description="Task not found"
          style={{ marginTop: '50px' }}
        />
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <Button
            type="link"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/tasks')}
            style={{ marginRight: '16px' }}
          >
            Back
          </Button>
          {status && <h1 style={{ margin: 0, display: 'inline-block' }}>{status.name}</h1>}
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            Refresh
          </Button>
          {status && status.status === 'pending' && (
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => handleTaskAction('start')}
            >
              Start
            </Button>
          )}
          {status && status.status === 'running' && (
            <>
              <Button
                icon={<PauseCircleOutlined />}
                onClick={() => handleTaskAction('pause')}
              >
                Pause
              </Button>
              <Button
                danger
                icon={<StopOutlined />}
                onClick={() => handleTaskAction('cancel')}
              >
                Cancel
              </Button>
            </>
          )}
          {status && status.status === 'paused' && (
            <>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => handleTaskAction('resume')}
              >
                Resume
              </Button>
              <Button
                danger
                icon={<StopOutlined />}
                onClick={() => handleTaskAction('cancel')}
              >
                Cancel
              </Button>
            </>
          )}
          {results.length > 0 && (
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExportResults}
            >
              Export
            </Button>
          )}
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* Status Card */}
        <Col span={24}>
          <Card>
            <Row gutter={[16, 16]}>
              <Col span={4}>
                <div style={{ textAlign: 'center' }}>
                  {getStatusIcon()}
                  <p style={{ marginTop: '8px', marginBottom: 0 }}>
                    <Tag color={getStatusColor()}>{status?.status.toUpperCase()}</Tag>
                  </p>
                  {!isConnected && (
                    <p style={{ fontSize: '12px', color: '#f5222d' }}>Disconnected</p>
                  )}
                </div>
              </Col>

              <Col span={20}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Statistic
                      title="Progress"
                      value={progress}
                      suffix="%"
                    />
                    <Progress
                      percent={progress}
                      status={
                        status?.status === 'failed' ? 'exception' : 'active'
                      }
                      style={{ marginTop: '8px' }}
                    />
                  </Col>
                  <Col span={12}>
                    {status?.current_step && (
                      <div>
                        <p style={{ margin: '0 0 8px 0', fontSize: '12px', color: '#8c8c8c' }}>
                          Current Step
                        </p>
                        <p style={{ margin: 0 }}>{status.current_step}</p>
                      </div>
                    )}
                  </Col>
                </Row>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* Details */}
        <Col span={24}>
          <Card title="Task Information">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic title="Task ID" value={status?.task_id} />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Created"
                  value={status?.started_at ? new Date(status.started_at).toLocaleString() : 'N/A'}
                />
              </Col>
              {status?.completed_at && (
                <Col span={12}>
                  <Statistic
                    title="Completed"
                    value={new Date(status.completed_at).toLocaleString()}
                  />
                </Col>
              )}
              {status?.progress === 100 && status?.started_at && status?.completed_at && (
                <Col span={12}>
                  <Statistic
                    title="Duration"
                    value={`${Math.round((new Date(status.completed_at).getTime() - new Date(status.started_at).getTime()) / 1000)} s`}
                  />
                </Col>
              )}
            </Row>
          </Card>
        </Col>

        {/* Tabs */}
        <Col span={24}>
          <Card>
            <Tabs
              items={[
                {
                  key: 'logs',
                  label: `Logs (${logs.length})`,
                  children: (
                    <div className="task-logs">
                      {logs.length === 0 ? (
                        <Empty
                          description="No logs yet"
                          style={{ marginTop: '24px' }}
                        />
                      ) : (
                        <List
                          dataSource={logs}
                          renderItem={(log: TaskLog, index) => (
                            <List.Item key={index}>
                              <span style={{ color: logColors[log.level] || '#000' }}>
                                [{log.level}] {new Date(log.timestamp).toLocaleTimeString()}
                              </span>
                              <br />
                              <span>{log.message}</span>
                            </List.Item>
                          )}
                          style={{
                            maxHeight: '400px',
                            overflowY: 'auto',
                            backgroundColor: '#f5f5f5',
                            padding: '12px',
                            borderRadius: '4px',
                          }}
                        />
                      )}
                    </div>
                  ),
                },
                {
                  key: 'results',
                  label: `Results (${results.length})`,
                  children: (
                    <div className="task-results">
                      {results.length === 0 ? (
                        <Empty
                          description="No results yet"
                          style={{ marginTop: '24px' }}
                        />
                      ) : (
                        <List
                          dataSource={results}
                          renderItem={(result: TaskResult, index) => (
                            <List.Item key={index}>
                              <Card style={{ width: '100%' }}>
                                <pre>{JSON.stringify(result, null, 2)}</pre>
                              </Card>
                            </List.Item>
                          )}
                        />
                      )}
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </Col>

        {/* Error Message */}
        {error && (
          <Col span={24}>
            <Result
              status="error"
              title="Error"
              subTitle={error}
            />
          </Col>
        )}

        {/* Completion Result */}
        {isCompleted && status?.status === 'completed' && (
          <Col span={24}>
            <Result
              status="success"
              title="Task Completed Successfully"
              subTitle={`Found ${results.length} results`}
              extra={
                <Button type="primary" onClick={handleExportResults}>
                  Export Results
                </Button>
              }
            />
          </Col>
        )}

        {isCompleted && status?.status === 'failed' && (
          <Col span={24}>
            <Result
              status="error"
              title="Task Failed"
              subTitle="An error occurred during task execution"
              extra={
                <Button onClick={handleRefresh}>
                  Retry
                </Button>
              }
            />
          </Col>
        )}
      </Row>
    </div>
  )
}

export default TaskDetail
