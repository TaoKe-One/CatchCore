/**
 * API client service
 */

import axios, { AxiosInstance, AxiosError } from 'axios'
import { TokenResponse, User } from '../types'

const API_BASE_URL = '/api/v1'

class ApiService {
  private api: AxiosInstance

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    })

    // Add response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  // Auth APIs
  async login(username: string, password: string): Promise<TokenResponse> {
    const response = await this.api.post('/auth/login', {
      username,
      password,
    })
    return response.data
  }

  async register(username: string, email: string, password: string, fullName?: string): Promise<User> {
    const response = await this.api.post('/auth/register', {
      username,
      email,
      password,
      full_name: fullName,
    })
    return response.data
  }

  async refresh(refreshToken: string): Promise<TokenResponse> {
    const response = await this.api.post('/auth/refresh', {
      refresh_token: refreshToken,
    })
    return response.data
  }

  // Asset APIs
  async getAssets(page: number = 1, pageSize: number = 20) {
    const response = await this.api.get('/assets', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  async getAsset(id: number) {
    const response = await this.api.get(`/assets/${id}`)
    return response.data
  }

  async createAsset(data: any) {
    const response = await this.api.post('/assets', data)
    return response.data
  }

  async updateAsset(id: number, data: any) {
    const response = await this.api.put(`/assets/${id}`, data)
    return response.data
  }

  async deleteAsset(id: number) {
    const response = await this.api.delete(`/assets/${id}`)
    return response.data
  }

  // Task APIs
  async getTasks(page: number = 1, pageSize: number = 20) {
    const response = await this.api.get('/tasks', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  async getTask(id: number) {
    const response = await this.api.get(`/tasks/${id}`)
    return response.data
  }

  async createTask(data: any) {
    const response = await this.api.post('/tasks', data)
    return response.data
  }

  async getVulnerabilities(page: number = 1, pageSize: number = 20) {
    const response = await this.api.get('/vulnerabilities', {
      params: { page, page_size: pageSize },
    })
    return response.data
  }

  async getVulnerability(id: number) {
    const response = await this.api.get(`/vulnerabilities/${id}`)
    return response.data
  }

  // Task control methods
  async startTask(taskId: number) {
    const response = await this.api.post(`/tasks/${taskId}/start`)
    return response.data
  }

  async pauseTask(taskId: number) {
    const response = await this.api.post(`/tasks/${taskId}/pause`)
    return response.data
  }

  async resumeTask(taskId: number) {
    const response = await this.api.post(`/tasks/${taskId}/resume`)
    return response.data
  }

  async cancelTask(taskId: number) {
    const response = await this.api.post(`/tasks/${taskId}/cancel`)
    return response.data
  }

  async deleteTask(taskId: number) {
    const response = await this.api.delete(`/tasks/${taskId}`)
    return response.data
  }

  async deleteAsset(assetId: number) {
    const response = await this.api.delete(`/assets/${assetId}`)
    return response.data
  }
}

export default new ApiService()
