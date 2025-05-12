import React, { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Paper,
  TextField,
  Typography,
  IconButton,
  CircularProgress
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import HistoryIcon from '@mui/icons-material/History';

import { sendChatMessage, addMessage, clearChat } from '../store/slices/chatSlice';
import type { RootState, AppDispatch } from '../store';
import type { ChatMessage } from '../api/chat';

const AIChat: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { messages, loading } = useSelector((state: RootState) => state.chat);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = () => {
    if (input.trim()) {
      // Add user message to the chat
      const userMessage: ChatMessage = {
        role: 'user',
        content: input.trim(),
      };
      
      dispatch(addMessage(userMessage));
      
      // Send message to the backend
      dispatch(sendChatMessage({
        messages: [...messages, userMessage],
      }));
      
      // Clear input
      setInput('');
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const handleClearChat = () => {
    dispatch(clearChat());
  };
  
  return (
    <Box sx={{ height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      {/* Chat header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">AI Chat</Typography>
        
        <Box>
          <IconButton onClick={handleClearChat} title="Clear chat">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>
      
      {/* Chat messages */}
      <Paper 
        elevation={0} 
        sx={{ 
          flex: 1, 
          p: 2, 
          overflowY: 'auto', 
          mb: 2, 
          display: 'flex', 
          flexDirection: 'column',
          bgcolor: '#f5f0ff'
        }}
      >
        {messages.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
            <HistoryIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="body1" color="text.secondary">
              No conversation history yet. Start chatting!
            </Typography>
          </Box>
        ) : (
          messages.map((msg: ChatMessage, index: number) => (
            <Box
              key={index}
              sx={{
                maxWidth: '80%',
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 2,
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'background.paper',
                  color: msg.role === 'user' ? 'white' : 'text.primary',
                  borderRadius: 2,
                }}
              >
                <Typography variant="body1">{msg.content}</Typography>
              </Paper>
            </Box>
          ))
        )}
        
        {/* Loading indicator when sending message */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Paper>
      
      {/* Input area */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          borderRadius: 4,
        }}
      >
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Ask AI Chat..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          multiline
          maxRows={4}
          disabled={loading}
          InputProps={{
            sx: { borderRadius: 4 }
          }}
        />
        <IconButton 
          color="primary" 
          onClick={handleSendMessage} 
          disabled={loading || !input.trim()}
          sx={{ ml: 1 }}
        >
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  );
};

export default AIChat;