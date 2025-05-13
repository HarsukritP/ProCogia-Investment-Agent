import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Chip,
  Menu,
  MenuItem,
  Card,
  CardContent
} from '@mui/material';
import { unstable_Grid as Grid } from '@mui/system';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

import { fetchPortfolios } from '../store/slices/portfolioSlice';
import type { RootState, AppDispatch } from '../store';

// Sample portfolio data (in a real app, this would come from the backend)
const sampleAssets = [
  { id: 1, name: 'Asset 1', type: 'Stock', unitPrice: 6.43, date: new Date('2025-05-02'), return: 3.45 },
  { id: 2, name: 'Asset 2', type: 'Govt. Bond', unitPrice: 2000, date: new Date('2025-04-22'), return: 42.34 },
  { id: 3, name: 'Asset 3', type: 'Private Bond', unitPrice: 1200, date: new Date('2025-02-28'), return: 3.44 },
  { id: 4, name: 'Asset 4', type: 'Stock', unitPrice: 17.2, date: new Date('2025-02-05'), return: -5.66 },
  { id: 5, name: 'Asset 5', type: 'Real Estate', unitPrice: 2000000, date: new Date('2025-01-25'), return: -0.06 },
  { id: 6, name: 'Asset 6', type: 'Stock', unitPrice: 21.2, date: new Date('2025-01-25'), return: -0.06 },
  { id: 7, name: 'Asset 7', type: 'Govt. Bond', unitPrice: 1000, date: new Date('2025-01-05'), return: -0.07 },
  { id: 8, name: 'Asset 8', type: 'Private Bond', unitPrice: 15000, date: new Date('2024-12-19'), return: 1.2 },
  { id: 9, name: 'Asset 9', type: 'Stock', unitPrice: 116, date: new Date('2024-10-23'), return: 1.11 }
];

// Mock allocation data for the chart
const allocationData = [
  { name: 'Stocks', value: 45, color: '#8884d8' },
  { name: 'Bonds', value: 30, color: '#82ca9d' },
  { name: 'Real Estate', value: 15, color: '#ffc658' },
  { name: 'Cash', value: 10, color: '#ff8042' }
];

const Portfolio: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { portfolios, loading } = useSelector((state: RootState) => state.portfolio);
  
  const [menuAnchorEl, setMenuAnchorEl] = useState<null | HTMLElement>(null);
  
  useEffect(() => {
    // Fetch portfolios if not already loaded
    if (portfolios.length === 0) {
      dispatch(fetchPortfolios());
    }
    
    // In a real app, we would fetch the current portfolio data here
  }, [dispatch, portfolios.length]);
  
  const handleMenuClose = () => {
    setMenuAnchorEl(null);
  };
  
  // Function to format date in a user-friendly way
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };
  
  // Function to format currency values
  const formatCurrency = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(2)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(2)}K`;
    } else {
      return `$${value.toFixed(2)}`;
    }
  };
  
  return (
    <Box sx={{ paddingY: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Portfolio</Typography>
      </Box>
      
      {/* Portfolio summary cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total Value
              </Typography>
              <Typography variant="h4">
                $1,245,320
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total Return
              </Typography>
              <Typography variant="h4" color="success.main">
                +8.4%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Risk Level
              </Typography>
              <Typography variant="h4">
                Moderate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Asset allocation chart */}
      <Paper elevation={0} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Asset Allocation</Typography>
        
        <Grid container spacing={2}>
          <Grid xs={12} md={4}>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={allocationData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                >
                  {allocationData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => `${value}%`} 
                  labelFormatter={() => ''} 
                />
              </PieChart>
            </ResponsiveContainer>
          </Grid>
          
          <Grid xs={12} md={8}>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {allocationData.map((item) => (
                <Chip
                  key={item.name}
                  label={`${item.name}: ${item.value}%`}
                  sx={{ 
                    bgcolor: item.color, 
                    color: 'white',
                    '& .MuiChip-label': { fontWeight: 'bold' }
                  }}
                />
              ))}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Assets table */}
      <Paper elevation={0} sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Assets</Typography>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell align="right">Unit Price</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell align="right">Return</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sampleAssets.map((asset) => (
                  <TableRow 
                    key={asset.id}
                    sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                  >
                    <TableCell component="th" scope="row">
                      {asset.name}
                    </TableCell>
                    <TableCell>{asset.type}</TableCell>
                    <TableCell align="right">{formatCurrency(asset.unitPrice)}</TableCell>
                    <TableCell>{formatDate(asset.date)}</TableCell>
                    <TableCell 
                      align="right"
                      sx={{ 
                        color: asset.return > 0 ? 'success.main' : asset.return < 0 ? 'error.main' : 'text.primary',
                        fontWeight: 'bold'
                      }}
                    >
                      {asset.return > 0 ? '+' : ''}{asset.return}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
        
        {/* Asset action menu */}
        <Menu
          anchorEl={menuAnchorEl}
          open={Boolean(menuAnchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleMenuClose}>View Details</MenuItem>
          <MenuItem onClick={handleMenuClose}>Edit Asset</MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: 'error.main' }}>Sell Asset</MenuItem>
        </Menu>
      </Paper>
    </Box>
  );
};

export default Portfolio;