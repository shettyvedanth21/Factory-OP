// React Query hooks for authentication
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { auth } from '../api/endpoints';
import { useAuthStore } from '../stores/authStore';
import { useUIStore } from '../stores/uiStore';

export const useLogin = () => {
  const setAuth = useAuthStore((state) => state.setAuth);
  const addNotification = useUIStore((state) => state.addNotification);
  const navigate = useNavigate();

  return useMutation({
    mutationFn: async ({ factory_id, email, password }: { factory_id: number; email: string; password: string }) => {
      return auth.login(factory_id, email, password);
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user, data.factory!);
      addNotification({
        type: 'success',
        title: 'Login successful',
        message: `Welcome back, ${data.user.email}`,
      });
      navigate('/dashboard');
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Login failed',
        message: error.message || 'Invalid credentials',
      });
    },
  });
};

export const useLogout = () => {
  const logout = useAuthStore((state) => state.logout);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return () => {
    logout();
    queryClient.clear();
    navigate('/login');
  };
};
