import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import marketService from '../../api/market';
import type { 
  MarketData, 
  NewsResponse,
  MarketAnalysis
} from '../../api/market';

// Types
interface MarketState {
  marketData: MarketData | null;
  marketNews: NewsResponse | null;
  marketAnalysis: MarketAnalysis | null;
  loading: boolean;
  error: string | null;
}

// Initial state
const initialState: MarketState = {
  marketData: null,
  marketNews: null,
  marketAnalysis: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchMarketData = createAsyncThunk(
  'market/fetchMarketData',
  async ({ symbols, indices }: { symbols?: string[], indices?: string[] }, { rejectWithValue }) => {
    try {
      return await marketService.getMarketData(symbols, indices);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch market data');
    }
  }
);

export const fetchMarketNews = createAsyncThunk(
  'market/fetchMarketNews',
  async ({ symbols, topics, days }: { symbols?: string[], topics?: string[], days?: number }, { rejectWithValue }) => {
    try {
      return await marketService.getMarketNews(symbols, topics, days);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch market news');
    }
  }
);

export const fetchMarketAnalysis = createAsyncThunk(
  'market/fetchMarketAnalysis',
  async (_, { rejectWithValue }) => {
    try {
      return await marketService.getMarketAnalysis();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch market analysis');
    }
  }
);

// Market slice
const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    clearMarketError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch market data
    builder.addCase(fetchMarketData.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchMarketData.fulfilled, (state, action) => {
      state.loading = false;
      state.marketData = action.payload;
    });
    builder.addCase(fetchMarketData.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch market news
    builder.addCase(fetchMarketNews.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchMarketNews.fulfilled, (state, action) => {
      state.loading = false;
      state.marketNews = action.payload;
    });
    builder.addCase(fetchMarketNews.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch market analysis
    builder.addCase(fetchMarketAnalysis.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchMarketAnalysis.fulfilled, (state, action) => {
      state.loading = false;
      state.marketAnalysis = action.payload;
    });
    builder.addCase(fetchMarketAnalysis.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
  },
});

export const { clearMarketError } = marketSlice.actions;

export default marketSlice.reducer;