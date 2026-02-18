// UI store with Zustand
import { create } from 'zustand';
import { AppNotification } from '../types';

interface UIState {
  sidebarOpen: boolean;
  notifications: AppNotification[];
}

interface UIActions {
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  addNotification: (notification: Omit<AppNotification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
}

type UIStore = UIState & UIActions;

// Generate unique ID for notifications
const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

export const useUIStore = create<UIStore>((set) => ({
  // Initial state
  sidebarOpen: true,
  notifications: [],

  // Actions
  toggleSidebar: () => {
    set((state) => ({ sidebarOpen: !state.sidebarOpen }));
  },

  setSidebarOpen: (open: boolean) => {
    set({ sidebarOpen: open });
  },

  addNotification: (notification) => {
    const id = generateId();
    set((state) => ({
      notifications: [
        ...state.notifications,
        { ...notification, id },
      ],
    }));

    // Auto-remove after 5 seconds for non-error notifications
    if (notification.type !== 'error') {
      setTimeout(() => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      }, 5000);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  clearAllNotifications: () => {
    set({ notifications: [] });
  },
}));
