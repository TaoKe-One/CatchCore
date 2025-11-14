import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import apiService from '../../services/api'
import { Asset } from '../../types'

interface AssetState {
  assets: Asset[]
  selectedAsset: Asset | null
  loading: boolean
  error: string | null
  total: number
  page: number
}

const initialState: AssetState = {
  assets: [],
  selectedAsset: null,
  loading: false,
  error: null,
  total: 0,
  page: 1,
}

export const fetchAssets = createAsyncThunk(
  'asset/fetchAssets',
  async ({ page, pageSize }: { page: number; pageSize: number }, { rejectWithValue }) => {
    try {
      const response = await apiService.getAssets(page, pageSize)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch assets')
    }
  }
)

export const fetchAssetDetail = createAsyncThunk(
  'asset/fetchAssetDetail',
  async (id: number, { rejectWithValue }) => {
    try {
      const response = await apiService.getAsset(id)
      return response.data
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch asset')
    }
  }
)

const assetSlice = createSlice({
  name: 'asset',
  initialState,
  reducers: {
    clearSelectedAsset: (state) => {
      state.selectedAsset = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAssets.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(
        fetchAssets.fulfilled,
        (state, action: PayloadAction<{ items: Asset[]; total: number; page: number }>) => {
          state.loading = false
          state.assets = action.payload.items
          state.total = action.payload.total
          state.page = action.payload.page
        }
      )
      .addCase(fetchAssets.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchAssetDetail.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchAssetDetail.fulfilled, (state, action: PayloadAction<Asset>) => {
        state.loading = false
        state.selectedAsset = action.payload
      })
      .addCase(fetchAssetDetail.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { clearSelectedAsset } = assetSlice.actions
export default assetSlice.reducer
