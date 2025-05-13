import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Layout component
import Layout from './components/layout/Layout';

// Pages
import Dashboard from './pages/Dashboard.tsx';
import AIChat from './pages/AIChat.tsx';
import ActionLog from './pages/ActionLog.tsx';
import Portfolio from './pages/Portfolio.tsx';

const theme = createTheme({
  palette: {
    primary: {
      main: '#6446a8',
    },
    secondary: {
      main: '#19857b',
    },
    background: {
      default: '#f8f9fa',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<AIChat />} />
            <Route path="/action-log" element={<ActionLog />} />
            <Route path="/portfolio" element={<Portfolio />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;