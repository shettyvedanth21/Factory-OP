// Device Detail Page - Full implementation
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDevice, useUpdateDevice } from '../hooks/useDevices';
import { useKPIsLive } from '../hooks/useKPIs';
import { useAlerts } from '../hooks/useAlerts';
import { useResolveAlert } from '../hooks/useAlerts';
import KPICardGrid from '../components/kpi/KPICardGrid';
import TelemetryChart from '../components/charts/TelemetryChart';
import { DeviceUpdate } from '../types';

const DeviceDetail = () => {
  const { deviceId } = useParams<{ deviceId: string }>();
  const navigate = useNavigate();
  const deviceIdNum = parseInt(deviceId || '0');
  
  const { data: device, isLoading: deviceLoading } = useDevice(deviceIdNum);
  const { data: kpis } = useKPIsLive(deviceIdNum);
  const { data: alertsData } = useAlerts({ device_id: deviceIdNum, resolved: false, per_page: 5 });
  const resolveAlert = useResolveAlert();
  const updateDevice = useUpdateDevice();
  
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editForm, setEditForm] = useState<DeviceUpdate>({});

  // Initialize edit form when device loads
  useEffect(() => {
    if (device) {
      setEditForm({
        name: device.name,
        manufacturer: device.manufacturer,
        model: device.model,
        region: device.region,
      });
    }
  }, [device]);

  // Check if device is online (last seen < 10 minutes ago)
  const isOnline = () => {
    if (!device?.last_seen) return false;
    const lastSeen = new Date(device.last_seen);
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
    return lastSeen > tenMinutesAgo;
  };

  // Format relative time
  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    const days = Math.floor(hours / 24);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  };

  const handleSaveEdit = () => {
    updateDevice.mutate({ deviceId: deviceIdNum, data: editForm }, {
      onSuccess: () => setIsEditModalOpen(false),
    });
  };

  if (deviceLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!device) {
    return <div className="text-center text-gray-500">Device not found</div>;
  }

  return (
    <div className="space-y-8">
      {/* Section 1: Device Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">
                {device.name || device.device_key}
              </h1>
              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-sm rounded">
                {device.device_key}
              </span>
              <span className={`px-2 py-1 text-sm rounded ${
                isOnline() 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {isOnline() ? '● Online' : '● Offline'}
              </span>
            </div>
            
            <div className="flex flex-wrap gap-4 text-sm text-gray-600 mt-4">
              {device.region && (
                <span className="flex items-center gap-1">
                  📍 {device.region}
                </span>
              )}
              {(device.manufacturer || device.model) && (
                <span className="flex items-center gap-1">
                  🏭 {device.manufacturer} {device.model}
                </span>
              )}
              <span className="flex items-center gap-1">
                🕒 Last seen: {formatRelativeTime(device.last_seen)}
              </span>
            </div>
          </div>
          
          <button
            onClick={() => setIsEditModalOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Edit
          </button>
        </div>
      </div>

      {/* Section 2: KPI Cards */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Live Metrics</h2>
        <KPICardGrid deviceId={deviceIdNum} />
      </div>

      {/* Section 3: Telemetry Chart */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Telemetry History</h2>
        <TelemetryChart deviceId={deviceIdNum} parameters={[]} />
      </div>

      {/* Section 4: Recent Alerts */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Alerts</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {alertsData?.data && alertsData.data.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Message</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {alertsData.data.slice(0, 5).map((alert) => (
                  <tr key={alert.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                        alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                        alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatRelativeTime(alert.triggered_at)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {alert.message}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => resolveAlert.mutate(alert.id)}
                        disabled={resolveAlert.isPending}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Resolve
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-gray-500">
              No active alerts for this device
            </div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Edit Device</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={editForm.name || ''}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Manufacturer</label>
                <input
                  type="text"
                  value={editForm.manufacturer || ''}
                  onChange={(e) => setEditForm({ ...editForm, manufacturer: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Model</label>
                <input
                  type="text"
                  value={editForm.model || ''}
                  onChange={(e) => setEditForm({ ...editForm, model: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Region</label>
                <input
                  type="text"
                  value={editForm.region || ''}
                  onChange={(e) => setEditForm({ ...editForm, region: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 mt-1"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={updateDevice.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {updateDevice.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeviceDetail;
