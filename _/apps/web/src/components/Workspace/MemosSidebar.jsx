"use client";

import { useState, useEffect } from "react";
import {
  Search,
  FileText,
  Star,
  Calendar,
  User,
  LogOut,
  Plus,
  Trash2,
} from "lucide-react";
import useUser from "@/utils/useUser";
import useAuth from "@/utils/useAuth";

export default function MemosSidebar({
  onMemoSelect,
  onNewMemo,
  currentMemoId,
  refreshTrigger, // Add this prop to trigger refresh
}) {
  const { data: user, loading: userLoading } = useUser();
  const { signOut } = useAuth();
  const [memos, setMemos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("updated_at");

  const fetchMemos = async () => {
    if (!user) return;

    try {
      setLoading(true);
      const params = new URLSearchParams({
        sortBy,
        ...(searchQuery && { search: searchQuery }),
      });

      const response = await fetch(`/api/user-memos?${params}`);
      const data = await response.json();

      if (data.success) {
        setMemos(data.memos);
        setError(null);
      } else {
        setError(data.error || "Failed to fetch memos");
      }
    } catch (err) {
      console.error("Error fetching memos:", err);
      setError("Failed to fetch memos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchMemos();
    }
  }, [user, searchQuery, sortBy]);

  // Add refresh effect when refreshTrigger changes
  useEffect(() => {
    if (user && refreshTrigger) {
      fetchMemos();
    }
  }, [refreshTrigger]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now - date;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return "Today";
    } else if (diffDays === 1) {
      return "Yesterday";
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const handleSignOut = async () => {
    await signOut({
      callbackUrl: "/",
      redirect: true,
    });
  };

  const handleDeleteMemo = async (memoId, memoTitle, event) => {
    // Prevent triggering the memo selection
    event.stopPropagation();

    if (
      !confirm(
        `Are you sure you want to delete "${memoTitle}"? This action cannot be undone.`,
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`/api/user-memos/${memoId}`, {
        method: "DELETE",
      });

      const data = await response.json();

      if (data.success) {
        // Refresh the memos list
        await fetchMemos();
        // If the deleted memo was currently selected, clear it
        if (currentMemoId === memoId) {
          onNewMemo();
        }
      } else {
        alert("Failed to delete memo: " + (data.error || "Unknown error"));
      }
    } catch (error) {
      console.error("Error deleting memo:", error);
      alert("Failed to delete memo. Please try again.");
    }
  };

  if (userLoading) {
    return (
      <div className="w-80 bg-white border-r border-gray-200 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // This should not happen as the workspace should require auth
  }

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <User size={16} className="text-white" />
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {user.name || user.email}
              </p>
              <p className="text-xs text-gray-500">My Memos</p>
            </div>
          </div>
          <button
            onClick={handleSignOut}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md"
            title="Sign out"
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* New Memo Button */}
        <button
          onClick={onNewMemo}
          className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          <span>New Memo</span>
        </button>
      </div>

      {/* Search and Sort */}
      <div className="p-4 border-b border-gray-200 space-y-3">
        <div className="relative">
          <Search
            size={16}
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Search memos..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
        >
          <option value="updated_at">Recently Updated</option>
          <option value="created_at">Recently Created</option>
          <option value="title">Title A-Z</option>
        </select>
      </div>

      {/* Memos List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading memos...</p>
          </div>
        ) : error ? (
          <div className="p-4 text-center">
            <p className="text-sm text-red-600">{error}</p>
            <button
              onClick={fetchMemos}
              className="mt-2 text-sm text-blue-600 hover:text-blue-700"
            >
              Try again
            </button>
          </div>
        ) : memos.length === 0 ? (
          <div className="p-4 text-center">
            <FileText size={48} className="text-gray-300 mx-auto mb-3" />
            <p className="text-sm text-gray-600 mb-2">No memos yet</p>
            <p className="text-xs text-gray-500">
              {searchQuery
                ? "No memos match your search"
                : "Create your first memo to get started"}
            </p>
          </div>
        ) : (
          <div className="p-2">
            {memos.map((memo) => (
              <div
                key={memo.id}
                className={`relative group rounded-lg mb-2 transition-colors ${
                  currentMemoId === memo.id
                    ? "bg-blue-50 border border-blue-200"
                    : "border border-transparent hover:bg-gray-50"
                }`}
              >
                <button
                  onClick={() => onMemoSelect(memo)}
                  className="w-full text-left p-3"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-medium text-gray-900 text-sm line-clamp-2 flex-1 pr-2">
                      {memo.title}
                    </h3>
                    <div className="flex items-center space-x-1">
                      {memo.is_favorite && (
                        <Star
                          size={14}
                          className="text-yellow-500 flex-shrink-0"
                        />
                      )}
                      <button
                        onClick={(e) =>
                          handleDeleteMemo(memo.id, memo.title, e)
                        }
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-all"
                        title="Delete memo"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>

                  {memo.company_name && (
                    <p className="text-xs text-blue-600 mb-1">
                      {memo.company_name}
                    </p>
                  )}

                  <p className="text-xs text-gray-500 line-clamp-2 mb-2">
                    {memo.preview}...
                  </p>

                  <div className="flex items-center text-xs text-gray-400">
                    <Calendar size={12} className="mr-1" />
                    {formatDate(memo.updated_at)}
                  </div>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
