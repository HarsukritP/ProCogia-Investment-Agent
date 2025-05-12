import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  TextField,
  IconButton,
  MenuItem,
  Select,
  FormControl,
  Button,
  List,
  ListItem,
  ListItemText,
  CircularProgress
} from '@mui/material';
import Grid from '@mui/material/Unstable_Grid2'; // Using Grid2 instead of Grid
import SearchIcon from '@mui/icons-material/Search';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

import { fetchMarketData, fetchMarketAnalysis } from '../store/slices/marketSlice';
import { fetchPortfolios, fetchPortfolioSummary } from '../store/slices/portfolioSlice';
import type { RootState } from '../store';
import type { AppDispatch } from '../store';

const Dashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { marketData, marketAnalysis, loading: marketLoading } = useSelector((state: RootState) => state.market);
  const { portfolios, loading: portfolioLoading } = useSelector((state: RootState) => state.portfolio);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [marketIndex, setMarketIndex] = useState('NASDAQ');
  
  useEffect(() => {
    // Fetch initial data
    dispatch(fetchMarketData({ indices: ['NASDAQ', 'S&P 500', 'Dow Jones'] }));
    dispatch(fetchMarketAnalysis());
    dispatch(fetchPortfolios());
    
    // If there are portfolios, fetch the first one's summary
    if (portfolios.length > 0) {
      dispatch(fetchPortfolioSummary(portfolios[0].id));
    }
  }, [dispatch, portfolios.length]);
  
  // Sample AI recommended actions (in a real app, this would come from the backend)
  const recommendedActions = [
    {
      id: 1,
      title: "Rebalance portfolio to reduce risk exposure",
      description: "Your portfolio is currently exposed to high volatility. Consider rebalancing to reduce risk."
    },
    {
      id: 2,
      title: "Take advantage of recent tech sector dip",
      description: "The technology sector is showing signs of recovery after recent dip."
    },
    {
      id: 3,
      title: "Review holdings in financial sector",
      description: "Financial sector stocks may be impacted by recent interest rate changes."
    },
    {
      id: 4,
      title: "Consider increasing bond allocation",
      description: "Current market volatility suggests increasing your bond allocation for stability."
    }
  ];
  
  // Sample portfolio actions (in a real app, this would come from the backend)
  const portfolioActions = [
    {
      id: 1,
      title: "Reduce risk exposure",
      description: "Reduce equity allocation by 5% and increase bond allocation."
    },
    {
      id: 2,
      title: "Add exposure to emerging markets",
      description: "Consider adding 2-3% allocation to emerging market ETFs."
    },
    {
      id: 3,
      title: "Optimize cash reserves",
      description: "Current cash reserves exceed target. Consider redeploying 1-2%."
    },
    {
      id: 4,
      title: "Review high-yield dividend stocks",
      description: "Analyze performance of high-yield dividend stocks in portfolio."
    }
  ];
  
  const handleSearch = () => {
    if (searchQuery.trim()) {
      dispatch(fetchMarketData({ symbols: [searchQuery] }));
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };
  
  const handleMarketChange = (event: any) => {
    setMarketIndex(event.target.value);
    // You could fetch specific market data here
  };
  
  return (
    <Box sx={{ paddingY: 2 }}>
      <Grid container spacing={3}>
        {/* Stock search section */}
        <Grid xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%', mb: 3 }} elevation={0}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Stocks</Typography>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <Select
                  value={marketIndex}
                  onChange={handleMarketChange}
                  displayEmpty
                  variant="outlined"
                >
                  <MenuItem value="NASDAQ">NASDAQ</MenuItem>
                  <MenuItem value="S&P 500">S&P 500</MenuItem>
                  <MenuItem value="Dow Jones">Dow Jones</MenuItem>
                </Select>
              </FormControl>
            </Box>
            
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search current stock information"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              InputProps={{
                endAdornment: (
                  <IconButton onClick={handleSearch}>
                    <SearchIcon />
                  </IconButton>
                ),
              }}
              sx={{ mb: 3 }}
            />
            
            {marketLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : marketData?.stocks && marketData.stocks.length > 0 ? (
              <Box>
                {marketData.stocks.map((stock) => (
                  <Paper key={stock.symbol} sx={{ p: 2, mb: 2 }} elevation={1}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Box>
                        <Typography variant="h6">{stock.symbol}</Typography>
                        <Typography variant="body2" color="text.secondary">{stock.name}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="h6">${stock.current_price.toFixed(2)}</Typography>
                        <Typography 
                          variant="body2" 
                          color={stock.change_pct > 0 ? 'success.main' : 'error.main'}
                        >
                          {stock.change_pct > 0 ? '+' : ''}{stock.change_pct.toFixed(2)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                ))}
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <Typography variant="body1" color="text.secondary">
                  No Results. Try Again.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Trending section */}
        <Grid xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%', mb: 3 }} elevation={0}>
            <Typography variant="h6" sx={{ mb: 2 }}>Trending Stocks and News</Typography>
            
            {marketLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Box>
                {marketAnalysis?.market_summary && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>Market Summary</Typography>
                    <Typography variant="body2">{marketAnalysis.market_summary}</Typography>
                  </Box>
                )}
                
                {marketAnalysis?.key_drivers && marketAnalysis.key_drivers.length > 0 && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" gutterBottom>Key Market Drivers</Typography>
                    <List dense>
                      {marketAnalysis.key_drivers.slice(0, 3).map((driver, index) => (
                        <ListItem key={index} disablePadding sx={{ mb: 1 }}>
                          <ListItemText 
                            primary={driver.factor}
                            primaryTypographyProps={{ variant: 'body2' }}
                            secondary={`Impact: ${driver.impact}`}
                            secondaryTypographyProps={{ 
                              variant: 'caption',
                              color: driver.impact === 'positive' ? 'success.main' : 
                                    driver.impact === 'negative' ? 'error.main' : 'text.secondary'
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
                
                {/* You could add news items here as well */}
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* AI Recommended Actions section */}
        <Grid xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }} elevation={0}>
            <Typography variant="h6" sx={{ mb: 2 }}>AI Recommended Actions</Typography>
            
            <List>
              {recommendedActions.map((action) => (
                <React.Fragment key={action.id}>
                  <ListItem 
                    sx={{ 
                      bgcolor: 'rgba(100, 70, 168, 0.08)', 
                      borderRadius: 2, 
                      mb: 2,
                      display: 'flex',
                      justifyContent: 'space-between'
                    }}
                    disablePadding
                  >
                    <Box sx={{ p: 2 }}>
                      <Typography variant="subtitle2">{`"Action ${action.id}"`}</Typography>
                    </Box>
                    
                    <Button 
                      component={Link}
                      to="/chat"
                      endIcon={<OpenInNewIcon />}
                      variant="text"
                      sx={{ color: 'primary.main', mr: 1 }}
                    >
                      Perform Task with AI Chat
                    </Button>
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </Paper>
        </Grid>
        
        {/* Your Portfolio section */}
        <Grid xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }} elevation={0}>
            <Typography variant="h6" sx={{ mb: 2 }}>Your Portfolio</Typography>
            
            {portfolioLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <List>
                {portfolioActions.map((action) => (
                  <React.Fragment key={action.id}>
                    <ListItem 
                      sx={{ 
                        bgcolor: 'rgba(100, 70, 168, 0.08)', 
                        borderRadius: 2, 
                        mb: 2
                      }}
                      disablePadding
                    >
                      <Box sx={{ p: 2 }}>
                        <Typography variant="subtitle2">{`"Action ${action.id}"`}</Typography>
                      </Box>
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;