// Analytics Jobs Page
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalytics, useCreateAnalyticsJob } from '../hooks/useAnalytics';
import { useDevices } from '../hooks/useDevices';
import { AnalyticsJob } from '../types';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  complete: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const jobTypeLabels: Record<string, string> = {
  anomaly: 'Anomaly Detection',
  failure_prediction: 'Failure Prediction',
  energy_forecast: 'Energy Forecast',
  ai_copilot: 'AI Copilot',
};

const Analytics = () => {
  const navigate = useNavigate();
  const { data: jobs, isLoading } = useAnalytics();
  const { data: devicesData } = useDevices({ per_page: 100 });
  const createJob = useCreateAnalyticsJob();
  
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    job_type: 'anomaly' as const,
    mode: 'standard' as const,
    device_ids: [] as number[],
    date_range_start: '',
    date_range_end: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    await createJob.mutateAsync({
      job_type: formData.job_type,
      mode: formData.mode,
      device_ids: formData.device_ids,
      date_range_start: new Date(formData.date_range_start).toISOString(),
      date_range_end: new Date(formData.date_range_end).toISOString(),
    });
    
    setShowModal(false);
    setFormData({
      job_type: 'anomaly',
      mode: 'standard',
      device_ids: [],
      date_range_start: '',
      date_range_end: '',
    });
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          + New Analysis
        </button>
      </div>

      {/* Jobs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Devices</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date Range</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                </td>
              </tr>
            ) : (
              jobs?.data?.map((job: AnalyticsJob) => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {jobTypeLabels[job.job_type]}
                    </div>
                    <div className="text-xs text-gray-500 capitalize">{job.mode} mode</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[job.status]}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {job.device_ids.length} device{job.device_ids.length !== 1 ? 's' : ''}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(job.date_range_start).toLocaleDateString()} -
                    {new Date(job.date_range_end).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(job.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => navigate(`/analytics/${job.id}`)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
            {!isLoading && jobs?.data?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No analytics jobs yet. Create your first analysis to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* New Analysis Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-bold text-gray-900">New Analysis</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Mode */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Mode</label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="standard"
                      checked={formData.mode === 'standard'}
                      onChange={(e) => setFormData({ ...formData, mode: e.target.value as any })}
                      className="mr-2"
                    />
                    Standard
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="ai_copilot"
                      checked={formData.mode === 'ai_copilot'}
                      onChange={(e) => setFormData({ ...formData, mode: e.target.value as any })}
                      className="mr-2"
                    />
                    AI Copilot
                  </label>
                </div>
              </div>

              {/* Analysis Type (only for standard mode) */}
              {formData.mode === 'standard' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Analysis Type</label>
                  <select
                    value={formData.job_type}
                    onChange={(e) => setFormData({ ...formData, job_type: e.target.value as any })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  >
                    <option value="anomaly">Anomaly Detection</option>
                    <option value="failure_prediction">Failure Prediction</option>
                    <option value="energy_forecast">Energy Forecast</option>
                  </select>
                </div>
              )}

              {/* Device Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Devices</label>
                <div className="border border-gray-300 rounded-lg max-h-48 overflow-y-auto">
                  {devicesData?.data?.map((device: any) => (
                    <label key={device.id} className="flex items-center p-3 hover:bg-gray-50 border-b last:border-b-0">
                      <input
                        type="checkbox"
                        checked={formData.device_ids.includes(device.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData({ ...formData, device_ids: [...formData.device_ids, device.id] });
                          } else {
                            setFormData({ ...formData, device_ids: formData.device_ids.filter(id => id !== device.id) });
                          }
                        }}
                        className="mr-3"
                      />
                      <div>
                        <div className="font-medium">{device.name || device.device_key}</div>
                        <div className="text-sm text-gray-500">{device.device_key}</div>
                      </div>
                    </label>
                  ))}
                </div>
                <p className="text-sm text-gray-500 mt-1">{formData.device_ids.length} device(s) selected</p>
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                  <input
                    type="datetime-local"
                    value={formData.date_range_start}
                    onChange={(e) => setFormData({ ...formData, date_range_start: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                  <input
                    type="datetime-local"
                    value={formData.date_range_end}
                    onChange={(e) => setFormData({ ...formData, date_range_end: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    required
                  />
                </div>
              </div>

              {/* Buttons */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formData.device_ids.length === 0 || !formData.date_range_start || !formData.date_range_end}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Start Analysis
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
