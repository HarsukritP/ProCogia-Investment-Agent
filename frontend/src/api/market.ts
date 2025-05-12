import apiClient from './index';

// Types
export interface StockData {
  symbol: string;
  name: string;
  current_price: number;
  open_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  change_pct: number;
  timestamp: string;
}

export interface IndexData {
  current: number;
  prev_close: number;
  change_pct: number;
  timestamp: string;
  symbol: string;
  name: string;
}

export interface EconomicIndicator {
  name: string;
  value: number;
  previous_value: number;
  change: number;
  category: string;
  timestamp: string;
}

export interface SectorData {
  name: string;
  performance_mtd: number;
  performance_ytd: number;
  outlook: string;
}

export interface NewsItem {
  title: string;
  source: string;
  summary: string;
  url?: string;
  published_at: string;
  sentiment?: 'positive' | 'neutral' | 'negative';
  impact?: 'high' | 'medium' | 'low';
}

export interface MarketData {
  timestamp: string;
  stocks?: StockData[];
  indices: Record<string, IndexData>;
  economic_indicators: Record<string, any>;
  sectors?: Record<string, SectorData>;
}

export interface MarketAnalysis {
  timestamp: string;
  analysis_type: string;
  market_summary: string;
  indices_analysis: any;
  sector_analysis: any;
  economic_analysis: any;
  sentiment_analysis: any;
  market_outlook: any;
  key_drivers: any[];
  risk_factors: any[];
}

export interface NewsResponse {
  timestamp: string;
  news_items: NewsItem[];
  analysis: {
    sentiment_distribution: Record<string, number>;
    impact_distribution: Record<string, number>;
    overall_sentiment: string;
    primary_topics: Array<{ topic: string; count: number }>;
  };
}

// Market API services
const marketService = {
  // Get market data for specified symbols and indices
  getMarketData: async (symbols?: string[], indices?: string[]) => {
    const params: Record<string, any> = {};
    
    if (symbols) {
      params.symbols = symbols.join(',');
    }
    
    if (indices) {
      params.indices = indices.join(',');
    }
    
    const response = await apiClient.get<MarketData>('/market/data', { params });
    return response.data;
  },

  // Get market news with sentiment analysis
  getMarketNews: async (symbols?: string[], topics?: string[], days: number = 3) => {
    const params: Record<string, any> = { days };
    
    if (symbols) {
      params.symbols = symbols.join(',');
    }
    
    if (topics) {
      params.topics = topics.join(',');
    }
    
    const response = await apiClient.get<NewsResponse>('/market/news', { params });
    return response.data;
  },

  // Get comprehensive market analysis
  getMarketAnalysis: async () => {
    const response = await apiClient.get<MarketAnalysis>('/market/analysis');
    return response.data;
  }
};

export default marketService;