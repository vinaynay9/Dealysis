"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  Users,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

export default function UsageAdminPage() {
  const [stats, setStats] = useState(null);
  const [recentGenerations, setRecentGenerations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [days, setDays] = useState(30);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/track-usage?days=${days}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch stats: ${response.status}`);
      }

      const data = await response.json();
      setStats(data.statistics);
      setRecentGenerations(data.recent_generations);
      setError(null);
    } catch (err) {
      console.error("Error fetching usage stats:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [days]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const StatCard = ({ icon, title, value, subtitle, color = "blue" }) => (
    <div
      className="bg-white rounded-lg shadow-md p-6 border-l-4"
      style={{ borderLeftColor: color }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className="flex-shrink-0">
          <div
            className="p-3 rounded-full"
            style={{ backgroundColor: `${color}20` }}
          >
            {icon}
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading usage statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Error Loading Data
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={fetchStats}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const successRate = stats
    ? ((stats.successful_generations / stats.total_generations) * 100).toFixed(
        1,
      )
    : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Dealysis Usage Analytics
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Monitor memo generation activity and performance
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <select
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value))}
                className="border border-gray-300 rounded-md px-3 py-2 bg-white text-sm"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
              <button
                onClick={fetchStats}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<BarChart3 size={24} className="text-blue-600" />}
            title="Total Generations"
            value={stats?.total_generations || 0}
            subtitle={`${days} day period`}
            color="#3B82F6"
          />

          <StatCard
            icon={<Users size={24} className="text-green-600" />}
            title="Unique Companies"
            value={stats?.unique_companies || 0}
            subtitle="Different companies analyzed"
            color="#10B981"
          />

          <StatCard
            icon={<FileText size={24} className="text-purple-600" />}
            title="Avg Materials"
            value={stats?.avg_total_materials || 0}
            subtitle="Files + texts + URLs per memo"
            color="#8B5CF6"
          />

          <StatCard
            icon={<Clock size={24} className="text-orange-600" />}
            title="Avg Processing Time"
            value={
              stats?.avg_processing_time
                ? `${stats.avg_processing_time}s`
                : "0s"
            }
            subtitle="Time to generate memo"
            color="#F59E0B"
          />
        </div>

        {/* Success Rate */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Success Rate
            </h3>
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-gray-600">Successful</span>
                  <span className="text-sm font-medium text-green-600">
                    {stats?.successful_generations || 0}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${successRate}%` }}
                  ></div>
                </div>
                <div className="flex justify-between mt-2">
                  <span className="text-sm text-gray-600">Failed</span>
                  <span className="text-sm font-medium text-red-600">
                    {stats?.failed_generations || 0}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">
                  {successRate}%
                </div>
                <div className="text-sm text-gray-500">success rate</div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Average Files per Memo
            </h3>
            <div className="text-3xl font-bold text-blue-600">
              {stats?.avg_files_per_memo || 0}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              Uploaded documents only
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Quick Stats
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">
                  Most materials in one memo:
                </span>
                <span className="text-sm font-medium">
                  {Math.max(
                    ...recentGenerations.map(
                      (g) => g.total_reference_materials || 0,
                    ),
                    0,
                  )}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Recent activity:</span>
                <span className="text-sm font-medium">
                  {recentGenerations.length} generations
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Generations */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Recent Memo Generations
            </h3>
            <p className="text-sm text-gray-500">
              Latest {recentGenerations.length} memo generations
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Materials
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Generated At
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentGenerations.map((generation) => (
                  <tr key={generation.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {generation.company_name || "Unknown Company"}
                      </div>
                      <div className="text-sm text-gray-500">
                        ID: {generation.id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FileText size={16} className="text-gray-400 mr-2" />
                        <span className="text-sm text-gray-900">
                          {generation.total_reference_materials} materials
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {generation.generation_successful ? (
                          <>
                            <CheckCircle
                              size={16}
                              className="text-green-500 mr-2"
                            />
                            <span className="text-sm text-green-800">
                              Success
                            </span>
                          </>
                        ) : (
                          <>
                            <AlertCircle
                              size={16}
                              className="text-red-500 mr-2"
                            />
                            <span className="text-sm text-red-800">Failed</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(generation.generated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {recentGenerations.length === 0 && (
              <div className="text-center py-12">
                <BarChart3 size={48} className="text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">
                  No memo generations found for this period
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
