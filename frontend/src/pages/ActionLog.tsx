import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  List,
  CircularProgress
} from '@mui/material';

import type { RootState, AppDispatch } from '../store';
import { fetchPortfolios } from '../store/slices/portfolioSlice';

// Sample action log data (in a real app, this would come from the backend)
const actionLogData = [
  {
    id: 1,
    type: 'Optimized Assets',
    date: new Date('2025-05-02T12:00:00'),
    details: 'Portfolio optimized to reduce risk and improve returns.'
  },
  {
    id: 2,
    type: 'Assets Sold',
    date: new Date('2025-04-22T14:30:00'),
    details: 'Sold positions in underperforming assets.'
  },
  {
    id: 3,
    type: 'Bought Assets',
    date: new Date('2025-02-28T10:15:00'),
    details: 'Added new positions in emerging markets ETFs.'
  },
  {
    id: 4,
    type: 'Optimized Assets',
    date: new Date('2025-02-05T16:45:00'),
    details: 'Portfolio rebalanced to align with target allocations.'
  },
  {
    id: 5,
    type: 'Assets Sold',
    date: new Date('2025-01-25T09:30:00'),
    details: 'Reduced exposure to high-volatility tech stocks.'
  },
  {
    id: 6,
    type: 'Bought Assets',
    date: new Date('2025-01-25T09:15:00'),
    details: 'Increased bond allocation for stability.'
  },
  {
    id: 7,
    type: 'Optimized Assets',
    date: new Date('2025-01-05T11:00:00'),
    details: 'Year-end portfolio optimization performed.'
  },
  {
    id: 8,
    type: 'Assets Sold',
    date: new Date('2024-12-19T15:20:00'),
    details: 'Tax-loss harvesting trades executed.'
  },
  {
    id: 9,
    type: 'Bought Assets',
    date: new Date('2024-10-23T13:45:00'),
    details: 'Initial portfolio positions established.'
  }
];

const ActionLog: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { portfolios, loading } = useSelector((state: RootState) => state.portfolio);
  
  useEffect(() => {
    // Fetch portfolios if not already loaded
    if (portfolios.length === 0) {
      dispatch(fetchPortfolios());
    }
    
    // In a real app, we would fetch the action log here
    // For now, we'll use the sample data
  }, [dispatch, portfolios.length]);
  
  // Function to format date in a user-friendly way
  const formatDate = (date: Date) => {
    const now = new Date();
    const isCurrentYear = date.getFullYear() === now.getFullYear();
    
    if (isCurrentYear) {
      return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric' });
    } else {
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    }
  };
  
  // Group actions by type for easier rendering
  const actionsByType: Record<string, typeof actionLogData> = {};
  actionLogData.forEach(action => {
    if (!actionsByType[action.type]) {
      actionsByType[action.type] = [];
    }
    actionsByType[action.type].push(action);
  });
  
  return (
    <Box sx={{ paddingY: 2 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>Action Log</Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List sx={{ width: '100%' }}>
          {Object.entries(actionsByType).map(([type, actions]) => (
            <React.Fragment key={type}>
              {actions.map((action) => (
                <Paper 
                  key={action.id} 
                  elevation={0} 
                  sx={{ 
                    mb: 2, 
                    p: 2, 
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    bgcolor: 'rgba(100, 70, 168, 0.08)',
                    borderRadius: 2
                  }}
                >
                  <Box>
                    <Typography variant="subtitle1">{type}</Typography>
                  </Box>
                  
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body2" color="text.secondary">
                      {formatDate(action.date)}
                    </Typography>
                  </Box>
                </Paper>
              ))}
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );
};

export default ActionLog;