import apiClient from './index';

// Types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  portfolio_id?: number;
}

export interface ChatResponse {
  response: string;
  actions_taken?: string[];
  timestamp: string;
}

// Chat API services
const chatService = {
  // Send a message to the AI assistant
  sendMessage: async (request: ChatRequest) => {
    const response = await apiClient.post<ChatResponse>('/chat/', request);
    return response.data;
  }
};

export default chatService;