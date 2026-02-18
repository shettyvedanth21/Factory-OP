// Main Layout component
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useUIStore } from '../../stores/uiStore';

const MainLayout = () => {
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      
      <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
        {/* Top bar */}
        <header className="bg-white shadow-sm border-b border-gray-200 h-16 flex items-center px-6">
          <h2 className="text-xl font-semibold text-gray-800">FactoryOps AI</h2>
        </header>
        
        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
