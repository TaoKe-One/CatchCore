import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Table, Button, Card, Space, Badge, Select, Modal, Form, Input, Drawer, Popconfirm, message } from 'antd'
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  DeleteOutlined,
  FileTextOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { fetchTasks } from '../../store/slices/taskSlice'
import { RootState, AppDispatch } from '../../store'
import apiService from '../../services/api'

const TaskList: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useDispatch<AppDispatch>()
  const { tasks, loading, total, page } = useSelector((state: RootState) => state.task)

  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [filterType, setFilterType] = useState<string | undefined>()
  const [isCreateModalVisible, setIsCreateModalVisible] = useState(false)
  const [isDetailDrawerVisible, setIsDetailDrawerVisible] = useState(false)
  const [selectedTask, setSelectedTask] = useState<any>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    handleSearch(1)
  }, [dispatch])

  const handleSearch = (pageNum: number = 1) => {
    dispatch(fetchTasks({ page: pageNum, pageSize: 20 }))
  }

  const handleCreateTask = async (values: any) => {
    try {
      await apiService.createTask({
        ...values,
        priority: parseInt(values.priority),
      })
      message.success('任务创建成功')
      setIsCreateModalVisible(false)
      form.resetFields()
      handleSearch(1)
    } catch (error) {
      message.error('任务创建失败')
    }
  }

  const handleTaskAction = async (taskId: number, action: string) => {
    try {
      if (action === 'start') {
        await apiService.startTask(taskId)
        message.success('任务已启动')
      } else if (action === 'pause') {
        await apiService.pauseTask(taskId)
        message.success('任务已暂停')
      } else if (action === 'resume') {
        await apiService.resumeTask(taskId)
        message.success('任务已恢复')
      } else if (action === 'cancel') {
        await apiService.cancelTask(taskId)
        message.success('任务已取消')
      } else if (action === 'delete') {
        await apiService.deleteTask(taskId)
        message.success('任务已删除')
      }
      handleSearch(page)
    } catch (error) {
      message.error('操作失败')
    }
  }

  const statusColors: { [key: string]: string } = {
    pending: 'default',
    running: 'processing',
    paused: 'warning',
    completed: 'success',
    failed: 'error',
    cancelled: 'default',
  }

  const taskTypes: { [key: string]: string } = {
    port_scan: '端口扫描',
    service_identify: '服务识别',
    fingerprint: '指纹识别',
    poc_detection: 'POC 检测',
    password_crack: '密码破解',
    directory_scan: '目录扫描',
    url_scan: 'URL 扫描',
    custom: '自定义',
  }

  const columns = [
    { title: '任务名称', dataIndex: 'name', key: 'name', width: 150 },
    {
      title: '类型',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 100,
      render: (type: string) => taskTypes[type] || type,
    },
    { title: '目标', dataIndex: 'target_range', key: 'target_range', width: 120 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => <Badge status={statusColors[status] as any} text={status} />,
    },
    { title: '优先级', dataIndex: 'priority', key: 'priority', width: 60 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'action',
      width: 200,
      fixed: 'right' as const,
      render: (_: any, record: any) => {
        const isRunning = record.status === 'running'
        const isPaused = record.status === 'paused'
        const isPending = record.status === 'pending'

        return (
          <Space size="small" wrap>
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/tasks/${record.id}`)}
            >
              查看
            </Button>
            {isPending && (
              <Button
                type="link"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleTaskAction(record.id, 'start')}
              >
                启动
              </Button>
            )}
            {isRunning && (
              <Button
                type="link"
                size="small"
                icon={<PauseCircleOutlined />}
                onClick={() => handleTaskAction(record.id, 'pause')}
              >
                暂停
              </Button>
            )}
            {isPaused && (
              <Button
                type="link"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleTaskAction(record.id, 'resume')}
              >
                恢复
              </Button>
            )}
            {(isRunning || isPending || isPaused) && (
              <Button
                type="link"
                danger
                size="small"
                icon={<StopOutlined />}
                onClick={() => handleTaskAction(record.id, 'cancel')}
              >
                取消
              </Button>
            )}
            <Button
              type="link"
              size="small"
              icon={<FileTextOutlined />}
              onClick={() => {
                setSelectedTask(record)
                setIsDetailDrawerVisible(true)
              }}
            >
              日志
            </Button>
            <Popconfirm
              title="确定删除？"
              onConfirm={() => handleTaskAction(record.id, 'delete')}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" danger size="small" icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        )
      },
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="任务管理"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsCreateModalVisible(true)}>
            新建任务
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="任务类型"
            style={{ width: 150 }}
            value={filterType}
            onChange={setFilterType}
            allowClear
          >
            <Select.Option value="port_scan">端口扫描</Select.Option>
            <Select.Option value="service_identify">服务识别</Select.Option>
            <Select.Option value="fingerprint">指纹识别</Select.Option>
            <Select.Option value="poc_detection">POC 检测</Select.Option>
          </Select>
          <Select
            placeholder="任务状态"
            style={{ width: 120 }}
            value={filterStatus}
            onChange={setFilterStatus}
            allowClear
          >
            <Select.Option value="pending">待处理</Select.Option>
            <Select.Option value="running">运行中</Select.Option>
            <Select.Option value="paused">已暂停</Select.Option>
            <Select.Option value="completed">已完成</Select.Option>
          </Select>
          <Button type="primary" onClick={() => handleSearch(1)}>
            筛选
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={tasks}
          loading={loading}
          pagination={{
            current: page,
            total: total,
            pageSize: 20,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (p) => handleSearch(p),
          }}
          rowKey="id"
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 创建任务 Modal */}
      <Modal
        title="创建新任务"
        visible={isCreateModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsCreateModalVisible(false)
          form.resetFields()
        }}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateTask}>
          <Form.Item name="name" label="任务名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="task_type" label="任务类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="port_scan">端口扫描</Select.Option>
              <Select.Option value="service_identify">服务识别</Select.Option>
              <Select.Option value="fingerprint">指纹识别</Select.Option>
              <Select.Option value="poc_detection">POC 检测</Select.Option>
              <Select.Option value="password_crack">密码破解</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="target_range" label="扫描目标" rules={[{ required: true }]}>
            <Input placeholder="IP 或 IP 段 (如 192.168.1.0/24)" />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="5">
            <Select>
              <Select.Option value="1">1 - 最低</Select.Option>
              <Select.Option value="5">5 - 中等</Select.Option>
              <Select.Option value="10">10 - 最高</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 任务日志 Drawer */}
      <Drawer
        title={`任务日志 - ${selectedTask?.name}`}
        placement="right"
        onClose={() => setIsDetailDrawerVisible(false)}
        open={isDetailDrawerVisible}
        width={600}
      >
        {selectedTask && (
          <div>
            <p>
              <strong>状态:</strong> {selectedTask.status}
            </p>
            <p>
              <strong>创建时间:</strong> {selectedTask.created_at}
            </p>
            <hr />
            <p>任务日志加载中...</p>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default TaskList
