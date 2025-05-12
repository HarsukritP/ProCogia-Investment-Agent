import apiClient from './index';

// Types
export interface Asset {
  id: number;
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  current_price: number;
  purchase_price: number;
  allocation: number;
  created_at: string;
  updated_at: string;
}

export interface Portfolio {
  id: number;
  name: string;
  description?: string;
  user_id: number;
  created_at: string;
  updated_at: string;
  assets: Asset[];
}

export interface PortfolioSummary {
  id: number;
  name: string;
  total_value: number;
  asset_allocation: Record<string, number>;
  performance: Record<string, number>;
  risk_metrics: Record<string, number>;
  top_holdings: Array<{
    symbol: string;
    name: string;
    value: number;
    allocation: number;
  }>;
}

export interface TradeRequest {
  portfolio_id: number;
  asset_id: number;
  trade_type: 'buy' | 'sell';
  quantity: number;
  price: number;
  commission?: number;
}

export interface OptimizationRequest {
  portfolio_id: number;
  target_risk: number;
  max_allocation_per_asset?: number;
  min_bonds_allocation?: number;
  max_alternatives_allocation?: number;
  liquidity_requirement?: number;
}

// Portfolio API services
const portfolioService = {
  // Get all portfolios
  getAllPortfolios: async () => {
    const response = await apiClient.get<Portfolio[]>('/portfolio/');
    return response.data;
  },

  // Get portfolio by ID
  getPortfolio: async (id: number) => {
    const response = await apiClient.get<Portfolio>(`/portfolio/${id}`);
    return response.data;
  },

  // Get portfolio summary
  getPortfolioSummary: async (id: number) => {
    const response = await apiClient.get<PortfolioSummary>(`/portfolio/${id}/summary`);
    return response.data;
  },

  // Get portfolio history
  getPortfolioHistory: async (id: number, days: number = 30) => {
    const response = await apiClient.get(`/portfolio/${id}/history`, {
      params: { days }
    });
    return response.data;
  },

  // Analyze portfolio risk
  analyzeRisk: async (id: number, riskThreshold: number = 0.5) => {
    const response = await apiClient.get(`/portfolio/${id}/risk`, {
      params: { risk_threshold: riskThreshold }
    });
    return response.data;
  },

  // Optimize portfolio
  optimizePortfolio: async (params: OptimizationRequest) => {
    const { portfolio_id, ...queryParams } = params;
    const response = await apiClient.get(`/portfolio/${portfolio_id}/optimize`, {
      params: queryParams
    });
    return response.data;
  },

  // Execute trade
  executeTrade: async (trade: TradeRequest) => {
    const { portfolio_id, ...tradeData } = trade;
    const response = await apiClient.post(`/portfolio/${portfolio_id}/trades`, tradeData);
    return response.data;
  },

  // Add asset to portfolio
  addAsset: async (portfolio_id: number, assetData: Partial<Asset>) => {
    const response = await apiClient.post(`/portfolio/${portfolio_id}/assets`, assetData);
    return response.data;
  }
};

export default portfolioService;