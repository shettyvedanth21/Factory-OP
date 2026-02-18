// Main App component with routing
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';

// Pages
import FactorySelect from './pages/FactorySelect';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Machines from './pages/Machines';
import DeviceDetail from './pages/DeviceDetail';
import Rules from './pages/Rules';
import RuleBuilder from './pages/RuleBuilder';
import Analytics from './pages/Analytics';
import Reports from './pages/Reports';
import Users from './pages/Users';

// Layout
import MainLayout from './components/ui/MainLayout';

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
    },
  },
});

// Protected Route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Super Admin Route wrapper
const SuperAdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, user } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (user?.role !== 'super_admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/factory-select" element={<FactorySelect />} />
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes with MainLayout */}
          <Route path="/" element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="machines" element={<Machines />} />
            <Route path="machines/:deviceId" element={<DeviceDetail />} />
            <Route path="rules" element={<Rules />} />
            <Route path="rules/new" element={<RuleBuilder />} />
            <Route path="rules/:ruleId" element={<RuleBuilder />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="reports" element={<Reports />} />
          </Route>
          
          {/* Super admin only routes */}
          <Route path="/users" element={
            <SuperAdminRoute>
              <MainLayout />
            </SuperAdminRoute>
          }>
            <Route index element={<Users />} />
          </Route>
          
          {/* Redirect unknown routes */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
