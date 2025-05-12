import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import chatService from '../../api/chat';
import type { ChatMessage, ChatRequest } from '../../api/chat';

// Types
interface ChatState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  actions: string[];
}

// Initial state
const initialState: ChatState = {
  messages: [],
  loading: false,
  error: null,
  actions: [],
};

// Async thunks
export const sendChatMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ messages, portfolioId }: { messages: ChatMessage[], portfolioId?: number }, { rejectWithValue }) => {
    try {
      const request: ChatRequest = {
        messages,
        portfolio_id: portfolioId,
      };
      return await chatService.sendMessage(request);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

// Chat slice
const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<ChatMessage>) => {
      state.messages.push(action.payload);
    },
    clearChat: (state) => {
      state.messages = [];
      state.actions = [];
    },
    clearChatError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Send message
    builder.addCase(sendChatMessage.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(sendChatMessage.fulfilled, (state, action) => {
      state.loading = false;
      // Add assistant's response to the chat
      state.messages.push({
        role: 'assistant',
        content: action.payload.response,
      });
      
      // Track any actions taken by the assistant
      if (action.payload.actions_taken) {
        state.actions = [...state.actions, ...action.payload.actions_taken];
      }
    });
    builder.addCase(sendChatMessage.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
      
      // Add error message as assistant's response
      state.messages.push({
        role: 'assistant',
        content: `Sorry, I encountered an error: ${action.payload}`,
      });
    });
  },
});

export const { addMessage, clearChat, clearChatError } = chatSlice.actions;

export default chatSlice.reducer;