import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import portfolioService from '../../api/portfolio';
import type { 
  Portfolio, 
  PortfolioSummary, 
  TradeRequest,
  OptimizationRequest
} from '../../api/portfolio';

// Types
interface PortfolioState {
  portfolios: Portfolio[];
  currentPortfolio: Portfolio | null;
  portfolioSummary: PortfolioSummary | null;
  portfolioHistory: any[];
  riskAnalysis: any | null;
  optimizationRecommendations: any | null;
  loading: boolean;
  error: string | null;
}

// Initial state
const initialState: PortfolioState = {
  portfolios: [],
  currentPortfolio: null,
  portfolioSummary: null,
  portfolioHistory: [],
  riskAnalysis: null,
  optimizationRecommendations: null,
  loading: false,
  error: null,
};

// Async thunks
export const fetchPortfolios = createAsyncThunk(
  'portfolio/fetchPortfolios',
  async (_, { rejectWithValue }) => {
    try {
      return await portfolioService.getAllPortfolios();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch portfolios');
    }
  }
);

export const fetchPortfolio = createAsyncThunk(
  'portfolio/fetchPortfolio',
  async (id: number, { rejectWithValue }) => {
    try {
      return await portfolioService.getPortfolio(id);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch portfolio');
    }
  }
);

export const fetchPortfolioSummary = createAsyncThunk(
  'portfolio/fetchPortfolioSummary',
  async (id: number, { rejectWithValue }) => {
    try {
      return await portfolioService.getPortfolioSummary(id);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch portfolio summary');
    }
  }
);

export const fetchPortfolioHistory = createAsyncThunk(
  'portfolio/fetchPortfolioHistory',
  async ({ id, days }: { id: number; days: number }, { rejectWithValue }) => {
    try {
      return await portfolioService.getPortfolioHistory(id, days);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch portfolio history');
    }
  }
);

export const analyzePortfolioRisk = createAsyncThunk(
  'portfolio/analyzePortfolioRisk',
  async ({ id, threshold }: { id: number; threshold: number }, { rejectWithValue }) => {
    try {
      return await portfolioService.analyzeRisk(id, threshold);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to analyze portfolio risk');
    }
  }
);

export const optimizePortfolio = createAsyncThunk(
  'portfolio/optimizePortfolio',
  async (params: OptimizationRequest, { rejectWithValue }) => {
    try {
      return await portfolioService.optimizePortfolio(params);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to optimize portfolio');
    }
  }
);

export const executeTrade = createAsyncThunk(
  'portfolio/executeTrade',
  async (trade: TradeRequest, { rejectWithValue }) => {
    try {
      return await portfolioService.executeTrade(trade);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to execute trade');
    }
  }
);

// Portfolio slice
const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setCurrentPortfolio: (state, action: PayloadAction<Portfolio | null>) => {
      state.currentPortfolio = action.payload;
    },
    clearPortfolioError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch portfolios
    builder.addCase(fetchPortfolios.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchPortfolios.fulfilled, (state, action) => {
      state.loading = false;
      state.portfolios = action.payload;
    });
    builder.addCase(fetchPortfolios.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch portfolio
    builder.addCase(fetchPortfolio.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchPortfolio.fulfilled, (state, action) => {
      state.loading = false;
      state.currentPortfolio = action.payload;
    });
    builder.addCase(fetchPortfolio.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch portfolio summary
    builder.addCase(fetchPortfolioSummary.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchPortfolioSummary.fulfilled, (state, action) => {
      state.loading = false;
      state.portfolioSummary = action.payload;
    });
    builder.addCase(fetchPortfolioSummary.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Fetch portfolio history
    builder.addCase(fetchPortfolioHistory.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchPortfolioHistory.fulfilled, (state, action) => {
      state.loading = false;
      state.portfolioHistory = action.payload;
    });
    builder.addCase(fetchPortfolioHistory.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Analyze portfolio risk
    builder.addCase(analyzePortfolioRisk.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(analyzePortfolioRisk.fulfilled, (state, action) => {
      state.loading = false;
      state.riskAnalysis = action.payload;
    });
    builder.addCase(analyzePortfolioRisk.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Optimize portfolio
    builder.addCase(optimizePortfolio.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(optimizePortfolio.fulfilled, (state, action) => {
      state.loading = false;
      state.optimizationRecommendations = action.payload;
    });
    builder.addCase(optimizePortfolio.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });

    // Execute trade
    builder.addCase(executeTrade.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(executeTrade.fulfilled, (state) => {
      state.loading = false;
      // We'll need to refresh the portfolio after a trade
    });
    builder.addCase(executeTrade.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
  },
});

export const { setCurrentPortfolio, clearPortfolioError } = portfolioSlice.actions;

export default portfolioSlice.reducer;