import React, { useState } from 'react';
import type { ReactNode } from 'react';
import { 
  Box, 
  CssBaseline, 
  Drawer, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemIcon, 
  ListItemText, 
  Toolbar, 
  Typography, 
  IconButton,
  useMediaQuery,
  useTheme
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import StarIcon from '@mui/icons-material/Star';
import ChatIcon from '@mui/icons-material/Chat';
import HistoryIcon from '@mui/icons-material/History';
import FolderIcon from '@mui/icons-material/Folder';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';

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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  // State for controlling sidebar expansion
  const [expanded, setExpanded] = useState(!isMobile);
  const [mobileOpen, setMobileOpen] = useState(false);
  
  // Drawer width based on expansion state
  const expandedWidth = 240;
  const collapsedWidth = 72;
  const drawerWidth = expanded ? expandedWidth : collapsedWidth;
  
  // Function to handle navigation
  const handleNavigation = (path: string) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };
  
  // Toggle drawer expansion
  const toggleDrawer = () => {
    setExpanded(!expanded);
  };
  
  // Toggle mobile drawer
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };
  
  // Drawer content
  const drawerContent = (
    <>
      <Toolbar 
        sx={{ 
          paddingY: 2, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: expanded ? 'space-between' : 'center',
          minHeight: 64
        }}
      >
        {expanded && (
          <Typography variant="h6" noWrap component="div" fontWeight="bold">
            Portfolio AI
          </Typography>
        )}
        <IconButton onClick={toggleDrawer} sx={{ display: { xs: 'none', md: 'flex' } }}>
          {expanded ? <ChevronLeftIcon /> : <MenuIcon />}
        </IconButton>
      </Toolbar>
      
      <List>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem 
              key={item.name} 
              disablePadding
              sx={{
                backgroundColor: isActive ? 'rgba(100, 70, 168, 0.08)' : 'transparent',
                borderRadius: 2,
                margin: '0.5rem',
                width: 'auto',
              }}
            >
              <ListItemButton 
                onClick={() => handleNavigation(item.path)}
                sx={{ 
                  borderRadius: 2,
                  justifyContent: expanded ? 'initial' : 'center',
                  '&:hover': {
                    backgroundColor: isActive ? 'rgba(100, 70, 168, 0.15)' : 'rgba(100, 70, 168, 0.08)',
                  }
                }}
              >
                <ListItemIcon sx={{ color: '#6446a8', minWidth: expanded ? 40 : 24 }}>
                  {item.icon}
                </ListItemIcon>
                {expanded && (
                  <ListItemText 
                    primary={item.name} 
                    primaryTypographyProps={{ 
                      fontWeight: isActive ? 'bold' : 'normal',
                      fontSize: '0.9rem'
                    }} 
                  />
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
              justifyContent: expanded ? 'initial' : 'center',
              '&:hover': {
                backgroundColor: 'rgba(100, 70, 168, 0.08)',
              }
            }}
          >
            <ListItemIcon sx={{ color: '#6446a8', minWidth: expanded ? 40 : 24 }}>
              <AccountCircleIcon />
            </ListItemIcon>
            {expanded && (
              <ListItemText 
                primary="User1" 
                primaryTypographyProps={{ 
                  fontSize: '0.9rem'
                }} 
              />
            )}
          </ListItemButton>
        </ListItem>
      </Box>
    </>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* Mobile drawer toggle */}
      {isMobile && (
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{ 
            position: 'fixed', 
            top: 10, 
            left: 10, 
            zIndex: 1300,
            backgroundColor: 'white',
            boxShadow: '0 0 10px rgba(0,0,0,0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.9)',
            }
          }}
        >
          <MenuIcon />
        </IconButton>
      )}
      
      {/* Mobile sidebar */}
      {isMobile && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { 
              width: expandedWidth, 
              boxSizing: 'border-box',
              bgcolor: '#f5f0ff',
              borderRight: 'none'
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}
      
      {/* Desktop sidebar */}
      <Drawer
        variant="permanent"
        open={expanded}
        sx={{
          display: { xs: 'none', md: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          [`& .MuiDrawer-paper`]: { 
            width: drawerWidth, 
            boxSizing: 'border-box',
            bgcolor: '#f5f0ff',
            borderRight: 'none',
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
            overflowX: 'hidden'
          },
        }}
      >
        {drawerContent}
      </Drawer>
      
      {/* Main content */}
      <Box
        component="main"
        sx={{ 
          flexGrow: 1, 
          p: 3, 
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          backgroundColor: '#f8f9fa',
          minHeight: '100vh',
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
        }}
      >
        <Toolbar sx={{ display: { xs: 'block', md: 'none' }, minHeight: '64px' }} />
        {children}
      </Box>
    </Box>
  );
};

export default Layout;