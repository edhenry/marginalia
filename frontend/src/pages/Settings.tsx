import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Bell, BookOpen, Link2 } from 'lucide-react';
import { contextApi } from '../services/api';
import { useState, useEffect } from 'react';
import type { UserPreferences } from '../types';

export default function Settings() {
  const queryClient = useQueryClient();

  const { data: preferences, isLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: contextApi.getPreferences,
  });

  const [formData, setFormData] = useState<Partial<UserPreferences>>({});

  useEffect(() => {
    if (preferences) {
      setFormData(preferences);
    }
  }, [preferences]);

  const updateMutation = useMutation({
    mutationFn: (data: Partial<UserPreferences>) =>
      contextApi.updatePreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
    },
  });

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4" />
          <div className="h-64 bg-gray-200 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500">Configure your research workspace</p>
        </div>

        <button
          onClick={handleSave}
          disabled={updateMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          <Save size={18} />
          {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {updateMutation.isSuccess && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          Settings saved successfully!
        </div>
      )}

      <div className="space-y-8">
        {/* Prioritization Weights */}
        <section className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen size={20} className="text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">
              Prioritization Weights
            </h2>
          </div>

          <p className="text-sm text-gray-500 mb-4">
            Adjust how Claude prioritizes papers in your queue. Values should sum
            to 1.0.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Relevance to Research Questions
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formData.weight_relevance || 0}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    weight_relevance: parseFloat(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Recency
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formData.weight_recency || 0}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    weight_recency: parseFloat(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Foundational Importance
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formData.weight_foundational || 0}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    weight_foundational: parseFloat(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Social Signal
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formData.weight_social || 0}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    weight_social: parseFloat(e.target.value),
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </section>

        {/* Notification Preferences */}
        <section className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <Bell size={20} className="text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Push Notifications</p>
                <p className="text-sm text-gray-500">
                  Receive push notifications for important updates
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.push_enabled || false}
                  onChange={(e) =>
                    setFormData({ ...formData, push_enabled: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600" />
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">Email Notifications</p>
                <p className="text-sm text-gray-500">Receive email updates</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.email_enabled || false}
                  onChange={(e) =>
                    setFormData({ ...formData, email_enabled: e.target.checked })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600" />
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email Digest
              </label>
              <select
                value={formData.email_digest || 'none'}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    email_digest: e.target.value as 'none' | 'daily' | 'weekly',
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="none">None</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          </div>
        </section>

        {/* Integrations */}
        <section className="bg-white p-6 rounded-lg border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <Link2 size={20} className="text-primary-600" />
            <h2 className="text-lg font-semibold text-gray-900">Integrations</h2>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Notion</p>
                  <p className="text-sm text-gray-500">
                    Sync your reading queue with Notion
                  </p>
                </div>
                <span className="px-2 py-1 text-xs font-medium text-gray-500 bg-gray-200 rounded">
                  Configure in .env
                </span>
              </div>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Obsidian</p>
                  <p className="text-sm text-gray-500">
                    Save literature notes to your vault
                  </p>
                </div>
                <span className="px-2 py-1 text-xs font-medium text-gray-500 bg-gray-200 rounded">
                  Configure in .env
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
