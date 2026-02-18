// Reports Page
import { useState } from 'react';
import { useReportsList, useCreateReport, useDownloadReport, useDeleteReport } from '../hooks/useReports';
import { useDevices } from '../hooks/useDevices';
import { Report, CreateReportRequest } from '../types';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  complete: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const formatLabels: Record<string, string> = {
  pdf: 'PDF',
  excel: 'Excel',
  json: 'JSON',
};

const Reports = () => {
  const { data: reportsData, isLoading } = useReportsList({ per_page: 50 });
  const { data: devicesData } = useDevices({ per_page: 100 });
  const createReport = useCreateReport();
  const downloadReport = useDownloadReport();
  const deleteReport = useDeleteReport();

  const [showModal, setShowModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [formData, setFormData] = useState<CreateReportRequest>({
    title: '',
    device_ids: [],
    date_range_start: '',
    date_range_end: '',
    format: 'pdf',
    include_analytics: false,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await createReport.mutateAsync(formData);

    setShowModal(false);
    setFormData({
      title: '',
      device_ids: [],
      date_range_start: '',
      date_range_end: '',
      format: 'pdf',
      include_analytics: false,
    });
  };

  const handleDownload = async (report: Report) => {
    await downloadReport.mutateAsync(report.id);
  };

  const handleDelete = async (reportId: string) => {
    if (window.confirm('Are you sure you want to delete this report?')) {
      await deleteReport.mutateAsync(reportId);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  const filteredReports = reportsData?.data?.filter((report: Report) => {
    if (!filterStatus) return true;
    return report.status === filterStatus;
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <button
          onClick={() => setShowModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          + Generate Report
        </button>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <label className="text-sm font-medium text-gray-700 mr-2">Filter by status:</label>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-1 text-sm"
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="complete">Complete</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Format</th>
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
                <td colSpan={7} className="px-6 py-4 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                </td>
              </tr>
            ) : (
              filteredReports?.map((report: Report) => (
                <tr key={report.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {report.title || report.id.slice(0, 8)}
                    </div>
                    {report.include_analytics && (
                      <span className="text-xs text-gray-500">With analytics</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">{formatLabels[report.format]}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColors[report.status]}`}>
                      {report.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {report.device_ids.length} device{report.device_ids.length !== 1 ? 's' : ''}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(report.date_range_start).toLocaleDateString()} -
                    {new Date(report.date_range_end).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(report.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {report.status === 'complete' && (
                      <button
                        onClick={() => handleDownload(report)}
                        disabled={downloadReport.isPending}
                        className="text-blue-600 hover:text-blue-900 mr-4 disabled:opacity-50"
                      >
                        {downloadReport.isPending ? 'Downloading...' : 'Download'}
                      </button>
                    )}
                    {(report.status === 'pending' || report.status === 'failed') && (
                      <button
                        onClick={() => handleDelete(report.id)}
                        disabled={deleteReport.isPending}
                        className="text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
            {!isLoading && filteredReports?.length === 0 && (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  No reports yet. Generate your first report to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Generate Report Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-bold text-gray-900">Generate Report</h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Report Title (optional)</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="e.g., Monthly Energy Report"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>

              {/* Format */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
                <select
                  value={formData.format}
                  onChange={(e) => setFormData({ ...formData, format: e.target.value as 'pdf' | 'excel' | 'json' })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="pdf">PDF</option>
                  <option value="excel">Excel</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              {/* Include Analytics */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.include_analytics}
                    onChange={(e) => setFormData({ ...formData, include_analytics: e.target.checked })}
                    className="mr-2"
                  />
                  Include analytics insights
                </label>
              </div>

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
                  disabled={formData.device_ids.length === 0 || !formData.date_range_start || !formData.date_range_end || createReport.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {createReport.isPending ? 'Creating...' : 'Generate Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
