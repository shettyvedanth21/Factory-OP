// Machines List Page with search
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDevices } from '../hooks/useDevices';
import { DeviceListItem } from '../types';

// Debounce hook
const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Device Card Component
const DeviceCard = ({ device }: { device: DeviceListItem }) => {
  const navigate = useNavigate();

  const isOnline = () => {
    if (!device.last_seen) return false;
    const lastSeen = new Date(device.last_seen);
    const tenMinutesAgo = new Date(Date.now() - 10 * 60 * 1000);
    return lastSeen > tenMinutesAgo;
  };

  const formatRelativeTime = (timestamp?: string) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div 
      onClick={() => navigate(`/machines/${device.id}`)}
      className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer p-6 border border-gray-200"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {device.name || device.device_key}
          </h3>
          <p className="text-sm text-gray-500">{device.device_key}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 text-xs rounded-full ${
            isOnline() 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {isOnline() ? 'Online' : 'Offline'}
          </span>
          {device.active_alert_count > 0 && (
            <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
              {device.active_alert_count} alert{device.active_alert_count > 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      <div className="space-y-2 text-sm text-gray-600">
        {device.region && (
          <div className="flex items-center gap-2">
            <span>📍</span>
            <span>{device.region}</span>
          </div>
        )}
        {(device.manufacturer || device.model) && (
          <div className="flex items-center gap-2">
            <span>🏭</span>
            <span>{device.manufacturer} {device.model}</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <span>🕒</span>
          <span>Last seen: {formatRelativeTime(device.last_seen)}</span>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between items-center">
        <div className="text-sm">
          <span className="text-gray-500">Health: </span>
          <span className={`font-semibold ${
            device.health_score >= 80 ? 'text-green-600' :
            device.health_score >= 60 ? 'text-yellow-600' :
            'text-red-600'
          }`}>
            {device.health_score}%
          </span>
        </div>
        <Link 
          to={`/machines/${device.id}`}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          onClick={(e) => e.stopPropagation()}
        >
          View Details →
        </Link>
      </div>
    </div>
  );
};

const Machines = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  const [page, setPage] = useState(1);
  
  const { data, isLoading } = useDevices({ 
    page, 
    per_page: 12, 
    search: debouncedSearch || undefined 
  });

  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Machines</h1>
        
        {/* Search Input */}
        <div className="w-full sm:w-96">
          <div className="relative">
            <input
              type="text"
              placeholder="Search by name or device key..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full border border-gray-300 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
          </div>
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data?.data?.map((device) => (
              <DeviceCard key={device.id} device={device} />
            ))}
          </div>

          {/* Pagination */}
          {data && data.total > 0 && (
            <div className="mt-8 flex justify-center items-center gap-4">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                ← Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {Math.ceil(data.total / 12)}
              </span>
              <button
                onClick={() => setPage(p => p + 1)}
                disabled={page * 12 >= data.total}
                className="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next →
              </button>
            </div>
          )}

          {data?.data?.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              {searchTerm ? 'No devices match your search' : 'No devices found'}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Machines;
