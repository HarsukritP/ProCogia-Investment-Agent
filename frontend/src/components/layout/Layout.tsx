import React from 'react';
import type { ReactNode } from 'react';
import { Box, CssBaseline, Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import StarIcon from '@mui/icons-material/Star';
import ChatIcon from '@mui/icons-material/Chat';
import HistoryIcon from '@mui/icons-material/History';
import FolderIcon from '@mui/icons-material/Folder';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

// Drawer width for the sidebar
const drawerWidth = 240;

// Navigation items configuration
const navItems = [
  { name: 'Dashboard', icon: <StarIcon />, path: '/' },
  { name: 'AI Chat', icon: <ChatIcon />, path: '/chat' },
  { name: 'Action Log', icon: <HistoryIcon />, path: '/action-log' },
  { name: 'Portfolio', icon: <FolderIcon />, path: '/portfolio' },
];

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Function to handle navigation
  const handleNavigation = (path: string) => {
    navigate(path);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { 
            width: drawerWidth, 
            boxSizing: 'border-box',
            bgcolor: '#f5f0ff',
            borderRight: 'none'
          },
        }}
      >
        <Toolbar sx={{ paddingTop: 2, paddingBottom: 2 }}>
          <Typography variant="h6" noWrap component="div" fontWeight="bold">
            Investment Portfolio AI
          </Typography>
        </Toolbar>
        
        <List>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <ListItem 
                key={item.name} 
                disablePadding
                sx={{
                  backgroundColor: isActive ? '#e9deff' : 'transparent',
                  borderRadius: 2,
                  margin: '0.5rem',
                  width: 'auto',
                }}
              >
                <ListItemButton 
                  onClick={() => handleNavigation(item.path)}
                  sx={{ 
                    borderRadius: 2,
                    '&:hover': {
                      backgroundColor: isActive ? '#e0d1ff' : '#f0e6ff',
                    }
                  }}
                >
                  <ListItemIcon sx={{ color: '#6446a8' }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText 
                    primary={item.name} 
                    primaryTypographyProps={{ 
                      fontWeight: isActive ? 'bold' : 'normal',
                      fontSize: '0.9rem'
                    }} 
                  />
                  {isActive && (
                    <Box sx={{ marginLeft: 1 }}>
                      <Typography variant="caption" sx={{ bgcolor: '#6446a8', color: 'white', borderRadius: 5, px: 1 }}>
                        3
                      </Typography>
                    </Box>
                  )}
                </ListItemButton>
              </ListItem>
            );
          })}
        </List>
        
        <Box sx={{ marginTop: 'auto', padding: 2 }}>
          <ListItem 
            disablePadding
            sx={{
              borderRadius: 2,
              margin: '0.5rem',
              width: 'auto',
            }}
          >
            <ListItemButton
              sx={{ 
                borderRadius: 2,
                '&:hover': {
                  backgroundColor: '#f0e6ff',
                }
              }}
            >
              <ListItemIcon sx={{ color: '#6446a8' }}>
                <AccountCircleIcon />
              </ListItemIcon>
              <ListItemText 
                primary="User1" 
                primaryTypographyProps={{ 
                  fontSize: '0.9rem'
                }} 
              />
            </ListItemButton>
          </ListItem>
        </Box>
      </Drawer>
      
      {/* Main content */}
      <Box
        component="main"
        sx={{ 
          flexGrow: 1, 
          p: 3, 
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: '#f8f9fa',
          minHeight: '100vh'
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout;