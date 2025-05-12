import { configureStore } from '@reduxjs/toolkit';
import portfolioReducer from './slices/portfolioSlice';
import marketReducer from './slices/marketSlice';
import chatReducer from './slices/chatSlice';

export const store = configureStore({
  reducer: {
    portfolio: portfolioReducer,
    market: marketReducer,
    chat: chatReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore non-serializable values in these paths
        ignoredActions: ['chat/messageReceived'],
        ignoredPaths: ['chat.messages'],
      },
    }),
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;