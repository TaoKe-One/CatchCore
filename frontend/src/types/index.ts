/**
 * Common type definitions
 */

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  avatar_url?: string
  is_active: boolean
  created_at: string
}

export interface Asset {
  id: number
  ip: string
  hostname?: string
  os?: string
  status: string
  department?: string
  environment?: string
  created_at: string
  updated_at: string
}

export interface Service {
  id: number
  port: number
  protocol?: string
  service_name?: string
  version?: string
  state: string
  discovered_at: string
}

export interface Task {
  id: number
  name: string
  task_type: string
  target_range: string
  status: string
  created_at: string
  started_at?: string
  finished_at?: string
  priority: number
}

export interface Vulnerability {
  id: number
  asset_id: number
  title: string
  description?: string
  cve_id?: string
  cvss_score?: number
  severity?: string
  status: string
  discovered_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface ApiResponse<T> {
  code: number
  message: string
  data?: T
}

export interface PaginationResponse<T> {
  code: number
  message: string
  data?: {
    items: T[]
    total: number
    page: number
    page_size: number
  }
}
