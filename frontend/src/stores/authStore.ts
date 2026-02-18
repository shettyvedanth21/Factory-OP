// Auth store with Zustand
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, Factory } from '../types';

interface AuthState {
  user: User | null;
  factory: Factory | null;
  token: string | null;
  isAuthenticated: boolean;
}

interface AuthActions {
  setAuth: (token: string, user: User, factory: Factory) => void;
  logout: () => void;
  clearAuth: () => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      // Initial state
      user: null,
      factory: null,
      token: null,
      isAuthenticated: false,

      // Actions
      setAuth: (token: string, user: User, factory: Factory) => {
        set({
          token,
          user,
          factory,
          isAuthenticated: true,
        });
        // Also store in sessionStorage for the current tab
        sessionStorage.setItem('factoryops_token', token);
        sessionStorage.setItem('factoryops_factory', JSON.stringify(factory));
        sessionStorage.setItem('factoryops_user', JSON.stringify(user));
      },

      logout: () => {
        set({
          user: null,
          factory: null,
          token: null,
          isAuthenticated: false,
        });
        // Clear sessionStorage
        sessionStorage.removeItem('factoryops_token');
        sessionStorage.removeItem('factoryops_factory');
        sessionStorage.removeItem('factoryops_user');
        sessionStorage.removeItem('selectedFactory');
      },

      clearAuth: () => {
        set({
          user: null,
          factory: null,
          token: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'factoryops-auth',
      storage: {
        getItem: (name) => {
          const str = sessionStorage.getItem(name);
          return str ? JSON.parse(str) : null;
        },
        setItem: (name, value) => {
          sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          sessionStorage.removeItem(name);
        },
      },
    }
  )
);

// Helper to check if user is super admin
export const useIsSuperAdmin = () => {
  return useAuthStore((state) => state.user?.role === 'super_admin');
};
