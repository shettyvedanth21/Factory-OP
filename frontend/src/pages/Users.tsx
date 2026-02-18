// Users Management Page
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUsersList, useInviteUser, useUpdateUserPermissions, useDeactivateUser } from '../hooks/useUsers';
import { useIsSuperAdmin } from '../stores/authStore';
import { FactoryUser, InviteUserRequest } from '../types';

const roleColors: Record<string, string> = {
  super_admin: 'bg-purple-100 text-purple-800',
  admin: 'bg-blue-100 text-blue-800',
};

const Users = () => {
  const navigate = useNavigate();
  const isSuperAdmin = useIsSuperAdmin();
  const { data: usersData, isLoading } = useUsersList();
  const inviteUser = useInviteUser();
  const updatePermissions = useUpdateUserPermissions();
  const deactivateUser = useDeactivateUser();

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<FactoryUser | null>(null);
  const [inviteForm, setInviteForm] = useState<InviteUserRequest>({
    email: '',
    whatsapp_number: '',
    permissions: {
      create_rules: true,
      run_analytics: true,
      generate_reports: true,
    },
  });
  const [editPermissions, setEditPermissions] = useState<Record<string, boolean>>({});

  if (!isSuperAdmin) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900">Access Denied</h2>
          <p className="text-gray-500 mt-2">You need super admin privileges to access this page.</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 text-blue-600 hover:text-blue-800"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    await inviteUser.mutateAsync(inviteForm);
    setShowInviteModal(false);
    setInviteForm({
      email: '',
      whatsapp_number: '',
      permissions: {
        create_rules: true,
        run_analytics: true,
        generate_reports: true,
      },
    });
  };

  const handleEditPermissions = async (userId: number) => {
    await updatePermissions.mutateAsync({ userId, permissions: editPermissions });
    setShowEditModal(false);
    setSelectedUser(null);
  };

  const handleDeactivate = async (userId: number) => {
    if (window.confirm('Are you sure you want to deactivate this user?')) {
      await deactivateUser.mutateAsync(userId);
    }
  };

  const openEditModal = (user: FactoryUser) => {
    setSelectedUser(user);
    setEditPermissions(user.permissions || {});
    setShowEditModal(true);
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
        <button
          onClick={() => setShowInviteModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          + Invite Admin
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Permissions</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Login</th>
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
              usersData?.data?.map((user: FactoryUser) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{user.email}</div>
                    {user.whatsapp_number && (
                      <div className="text-xs text-gray-500">{user.whatsapp_number}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${roleColors[user.role]}`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(user.permissions || {}).map(([key, value]) => (
                        value && (
                          <span key={key} className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                            {key.replace(/_/g, ' ')}
                          </span>
                        )
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(user.last_login)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {user.role !== 'super_admin' && (
                      <>
                        <button
                          onClick={() => openEditModal(user)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Edit
                        </button>
                        {user.is_active && (
                          <button
                            onClick={() => handleDeactivate(user.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Deactivate
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
            {!isLoading && usersData?.data?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No users yet. Invite your first admin to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-bold text-gray-900">Invite Admin</h2>
            </div>

            <form onSubmit={handleInvite} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <input
                  type="email"
                  value={inviteForm.email}
                  onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">WhatsApp Number (optional)</label>
                <input
                  type="text"
                  value={inviteForm.whatsapp_number || ''}
                  onChange={(e) => setInviteForm({ ...inviteForm, whatsapp_number: e.target.value })}
                  placeholder="+1234567890"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Permissions</label>
                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={inviteForm.permissions?.create_rules || false}
                      onChange={(e) => setInviteForm({
                        ...inviteForm,
                        permissions: { ...inviteForm.permissions!, create_rules: e.target.checked }
                      })}
                      className="mr-2"
                    />
                    Create Rules
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={inviteForm.permissions?.run_analytics || false}
                      onChange={(e) => setInviteForm({
                        ...inviteForm,
                        permissions: { ...inviteForm.permissions!, run_analytics: e.target.checked }
                      })}
                      className="mr-2"
                    />
                    Run Analytics
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={inviteForm.permissions?.generate_reports || false}
                      onChange={(e) => setInviteForm({
                        ...inviteForm,
                        permissions: { ...inviteForm.permissions!, generate_reports: e.target.checked }
                      })}
                      className="mr-2"
                    />
                    Generate Reports
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteUser.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {inviteUser.isPending ? 'Sending...' : 'Send Invite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Permissions Modal */}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b">
              <h2 className="text-xl font-bold text-gray-900">Edit Permissions</h2>
              <p className="text-sm text-gray-500 mt-1">{selectedUser.email}</p>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={editPermissions.create_rules || false}
                    onChange={(e) => setEditPermissions({ ...editPermissions, create_rules: e.target.checked })}
                    className="mr-2"
                  />
                  Create Rules
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={editPermissions.run_analytics || false}
                    onChange={(e) => setEditPermissions({ ...editPermissions, run_analytics: e.target.checked })}
                    className="mr-2"
                  />
                  Run Analytics
                </label>
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={editPermissions.generate_reports || false}
                    onChange={(e) => setEditPermissions({ ...editPermissions, generate_reports: e.target.checked })}
                    className="mr-2"
                  />
                  Generate Reports
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleEditPermissions(selectedUser.id)}
                  disabled={updatePermissions.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {updatePermissions.isPending ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
