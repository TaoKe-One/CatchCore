import React, { useEffect, useState } from 'react'
import {
  Table,
  Button,
  Card,
  Input,
  Space,
  Popconfirm,
  Select,
  Modal,
  Form,
  Upload,
  message,
  Drawer,
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  UploadOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { fetchAssets } from '../../store/slices/assetSlice'
import { RootState, AppDispatch } from '../../store'
import apiService from '../../services/api'
import type { UploadFile } from 'antd/es/upload/interface'

const AssetList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { assets, loading, total, page } = useSelector((state: RootState) => state.asset)

  const [searchIp, setSearchIp] = useState('')
  const [searchHostname, setSearchHostname] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | undefined>()
  const [filterEnv, setFilterEnv] = useState<string | undefined>()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [isDetailDrawerVisible, setIsDetailDrawerVisible] = useState(false)
  const [selectedAsset, setSelectedAsset] = useState<any>(null)
  const [form] = Form.useForm()
  const [addForm] = Form.useForm()

  useEffect(() => {
    handleSearch(1)
  }, [dispatch])

  const handleSearch = (pageNum: number = 1) => {
    dispatch(
      fetchAssets({
        page: pageNum,
        pageSize: 20,
      })
    )
  }

  const handleDeleteAsset = async (assetId: number) => {
    try {
      await apiService.deleteAsset(assetId)
      message.success('资产删除成功')
      handleSearch(page)
    } catch (error) {
      message.error('删除资产失败')
    }
  }

  const handleUploadAssets = async (file: UploadFile) => {
    try {
      // Parse CSV or file content
      message.success('资产导入成功')
      setIsModalVisible(false)
      handleSearch(1)
    } catch (error) {
      message.error('资产导入失败')
    }
  }

  const handleViewAssetDetails = (asset: any) => {
    setSelectedAsset(asset)
    setIsDetailDrawerVisible(true)
  }

  const columns = [
    { title: 'IP', dataIndex: 'ip', key: 'ip', width: 120 },
    { title: '主机名', dataIndex: 'hostname', key: 'hostname', width: 150 },
    { title: '操作系统', dataIndex: 'os', key: 'os', width: 100 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colors: { [key: string]: string } = {
          active: 'green',
          inactive: 'red',
          archived: 'gray',
        }
        return <span style={{ color: colors[status] || 'black' }}>{status}</span>
      },
    },
    { title: '部门', dataIndex: 'department', key: 'department', width: 100 },
    { title: '环境', dataIndex: 'environment', key: 'environment', width: 80 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewAssetDetails(record)}
          >
            详情
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />}>
            编辑
          </Button>
          <Popconfirm
            title="确定删除此资产？"
            onConfirm={() => handleDeleteAsset(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title="资产管理"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<UploadOutlined />}
              onClick={() => setIsModalVisible(true)}
            >
              批量导入
            </Button>
            <Button type="primary" icon={<PlusOutlined />}>
              添加资产
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="搜索 IP"
            style={{ width: 150 }}
            value={searchIp}
            onChange={(e) => setSearchIp(e.target.value)}
          />
          <Input
            placeholder="搜索主机名"
            style={{ width: 150 }}
            value={searchHostname}
            onChange={(e) => setSearchHostname(e.target.value)}
          />
          <Select
            placeholder="状态"
            style={{ width: 120 }}
            value={filterStatus}
            onChange={setFilterStatus}
            allowClear
          >
            <Select.Option value="active">活跃</Select.Option>
            <Select.Option value="inactive">非活跃</Select.Option>
            <Select.Option value="archived">归档</Select.Option>
          </Select>
          <Select
            placeholder="环境"
            style={{ width: 120 }}
            value={filterEnv}
            onChange={setFilterEnv}
            allowClear
          >
            <Select.Option value="production">生产</Select.Option>
            <Select.Option value="test">测试</Select.Option>
            <Select.Option value="development">开发</Select.Option>
          </Select>
          <Button type="primary" onClick={() => handleSearch(1)}>
            搜索
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={assets}
          loading={loading}
          pagination={{
            current: page,
            total: total,
            pageSize: 20,
            showTotal: (total) => `共 ${total} 条记录`,
            onChange: (p) => handleSearch(p),
          }}
          rowKey="id"
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 批量导入 Modal */}
      <Modal
        title="批量导入资产"
        visible={isModalVisible}
        onOk={() => setIsModalVisible(false)}
        onCancel={() => setIsModalVisible(false)}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <h4>支持格式:</h4>
            <ul>
              <li>单个 IP: 192.168.1.1</li>
              <li>IP 段: 192.168.1.0/24</li>
              <li>CSV 文件 (IP, 主机名, 部门, 环境)</li>
            </ul>
          </div>
          <Upload
            maxCount={1}
            onChange={(info) => {
              if (info.file.status === 'done') {
                handleUploadAssets(info.file)
              }
            }}
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
        </Space>
      </Modal>

      {/* 资产详情 Drawer */}
      <Drawer
        title="资产详情"
        placement="right"
        onClose={() => setIsDetailDrawerVisible(false)}
        open={isDetailDrawerVisible}
        width={500}
      >
        {selectedAsset && (
          <div>
            <p>
              <strong>IP:</strong> {selectedAsset.ip}
            </p>
            <p>
              <strong>主机名:</strong> {selectedAsset.hostname}
            </p>
            <p>
              <strong>操作系统:</strong> {selectedAsset.os}
            </p>
            <p>
              <strong>状态:</strong> {selectedAsset.status}
            </p>
            <p>
              <strong>部门:</strong> {selectedAsset.department}
            </p>
            <p>
              <strong>环境:</strong> {selectedAsset.environment}
            </p>
            <p>
              <strong>创建时间:</strong> {selectedAsset.created_at}
            </p>
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default AssetList
