// Dashboard Page with real-time summary
import { useDashboardSummary } from '../hooks/useDashboard';
import { useUIStore } from '../stores/uiStore';

const Dashboard = () => {
  const { data: summary, isLoading, dataUpdatedAt } = useDashboardSummary();
  const addNotification = useUIStore((state) => state.addNotification);

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getHealthScoreText = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatRelativeTime = (timestamp: number) => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  };

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-1/3"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500">
          Last updated: {formatRelativeTime(dataUpdatedAt)}
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Devices */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <span className="text-2xl">🔧</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Total Machines</p>
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
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-semibold">{summary?.active_devices || 0}</p>
            </div>
          </div>
        </div>

        {/* Offline Devices */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <span className="text-2xl">⚠️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Offline</p>
              <p className="text-2xl font-semibold">{summary?.offline_devices || 0}</p>
            </div>
          </div>
        </div>

        {/* Health Score */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className={`p-3 rounded-full ${getHealthScoreColor(summary?.health_score || 0)} bg-opacity-20`}>
              <span className="text-2xl">💚</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Health Score</p>
              <p className={`text-2xl font-semibold ${getHealthScoreText(summary?.health_score || 0)}`}>
                {summary?.health_score || 0}%
              </p>
            </div>
          </div>
        </div>

        {/* Active Alerts */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-orange-100 text-orange-600">
              <span className="text-2xl">🔔</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Active Alerts</p>
              <p className="text-2xl font-semibold">{summary?.active_alerts || 0}</p>
            </div>
          </div>
        </div>

        {/* Critical Alerts */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <span className="text-2xl">🚨</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Critical Alerts</p>
              <p className="text-2xl font-semibold">{summary?.critical_alerts || 0}</p>
            </div>
          </div>
        </div>

        {/* Current Energy */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
              <span className="text-2xl">⚡</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Current Energy</p>
              <p className="text-2xl font-semibold">
                {(summary?.current_energy_kw || 0).toFixed(1)} kW
              </p>
            </div>
          </div>
        </div>

        {/* Energy Today */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <span className="text-2xl">📊</span>
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Energy Today</p>
              <p className="text-2xl font-semibold">
                {(summary?.energy_today_kwh || 0).toFixed(0)} kWh
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
