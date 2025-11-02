export function LoadingState() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-gray-600">Loading memo...</p>
        <button
          onClick={() => (window.location.href = "/workspace")}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to Workspace
        </button>
      </div>
    </div>
  );
}
