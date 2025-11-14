import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import apiService from '../../services/api'
import { Task } from '../../types'

interface TaskState {
  tasks: Task[]
  selectedTask: Task | null
  loading: boolean
  error: string | null
  total: number
  page: number
}

const initialState: TaskState = {
  tasks: [],
  selectedTask: null,
  loading: false,
  error: null,
  total: 0,
  page: 1,
}

export const fetchTasks = createAsyncThunk(
  'task/fetchTasks',
  async ({ page, pageSize }: { page: number; pageSize: number }, { rejectWithValue }) => {
    try {
      const response = await apiService.getTasks(page, pageSize)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch tasks')
    }
  }
)

export const fetchTaskDetail = createAsyncThunk(
  'task/fetchTaskDetail',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await apiService.getTask(id)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch task')
    }
  }
)

const taskSlice = createSlice({
  name: 'task',
  initialState,
  reducers: {
    clearSelectedTask: (state) => {
      state.selectedTask = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTasks.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(
        fetchTasks.fulfilled,
        (state, action: PayloadAction<{ items: Task[]; total: number; page: number }>) => {
          state.loading = false
          state.tasks = action.payload.items
          state.total = action.payload.total
          state.page = action.payload.page
        }
      )
      .addCase(fetchTasks.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchTaskDetail.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchTaskDetail.fulfilled, (state, action: PayloadAction<Task>) => {
        state.loading = false
        state.selectedTask = action.payload
      })
      .addCase(fetchTaskDetail.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { clearSelectedTask } = taskSlice.actions
export default taskSlice.reducer
