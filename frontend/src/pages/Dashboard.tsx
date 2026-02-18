// Dashboard Page
import { useDashboardSummary } from '../hooks/useDashboard';

const Dashboard = () => {
  const { data: summary, isLoading } = useDashboardSummary();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Devices */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <span className="text-2xl">🔧</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Total Devices</p>
              <p className="text-2xl font-semibold">{summary?.total_devices || 0}</p>
            </div>
          </div>
        </div>

        {/* Active Devices */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <span className="text-2xl">✓</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Active Devices</p>
              <p className="text-2xl font-semibold">{summary?.active_devices || 0}</p>
            </div>
          </div>
        </div>

        {/* Health Score */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <span className="text-2xl">💚</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Health Score</p>
              <p className="text-2xl font-semibold">{summary?.health_score || 0}%</p>
            </div>
          </div>
        </div>

        {/* Active Alerts */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <span className="text-2xl">⚠️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Active Alerts</p>
              <p className="text-2xl font-semibold">{summary?.active_alerts || 0}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
