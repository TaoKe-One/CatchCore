import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'

import LoginPage from './pages/auth/LoginPage'
import Dashboard from './pages/dashboard/Dashboard'
import AssetList from './pages/assets/AssetList'
import TaskList from './pages/tasks/TaskList'
import VulnerabilityList from './pages/vulnerabilities/VulnerabilityList'

import './styles/App.less'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <Layout style={{ minHeight: '100vh' }}>
              <Dashboard />
            </Layout>
          }
        />
        <Route
          path="/assets"
          element={
            <Layout style={{ minHeight: '100vh' }}>
              <AssetList />
            </Layout>
          }
        />
        <Route
          path="/tasks"
          element={
            <Layout style={{ minHeight: '100vh' }}>
              <TaskList />
            </Layout>
          }
        />
        <Route
          path="/vulnerabilities"
          element={
            <Layout style={{ minHeight: '100vh' }}>
              <VulnerabilityList />
            </Layout>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Router>
  )
}

export default App
