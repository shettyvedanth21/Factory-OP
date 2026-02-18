// Sidebar component
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore, useIsSuperAdmin } from '../../stores/authStore';
import { useUIStore } from '../../stores/uiStore';
import { useLogout } from '../../hooks/useAuth';

const Sidebar = () => {
  const { user, factory, isAuthenticated } = useAuthStore();
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const toggleSidebar = useUIStore((state) => state.toggleSidebar);
  const isSuperAdmin = useIsSuperAdmin();
  const logout = useLogout();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
  };

  if (!isAuthenticated) return null;

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '📊' },
    { path: '/machines', label: 'Machines', icon: '🔧' },
    { path: '/rules', label: 'Rules', icon: '📋' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/reports', label: 'Reports', icon: '📄' },
  ];

  if (isSuperAdmin) {
    navItems.push({ path: '/users', label: 'Users', icon: '👥' });
  }

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
      
      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full bg-gray-900 text-white z-50 transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} w-64`}>
        {/* Factory name */}
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold">{factory?.name}</h1>
          <p className="text-sm text-gray-400">{factory?.slug}</p>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
              onClick={() => {
                if (window.innerWidth < 1024) {
                  toggleSidebar();
                }
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        
        {/* User info & logout */}
        <div className="p-4 border-t border-gray-800">
          <div className="mb-4">
            <p className="text-sm text-gray-300">{user?.email}</p>
            <span className="inline-block mt-1 px-2 py-1 text-xs bg-blue-600 rounded">
              {user?.role}
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            <span>🚪</span>
            <span>Logout</span>
          </button>
        </div>
      </aside>
      
      {/* Toggle button (mobile) */}
      <button
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-50 p-2 bg-gray-900 text-white rounded-lg lg:hidden"
      >
        {sidebarOpen ? '✕' : '☰'}
      </button>
    </>
  );
};

export default Sidebar;
