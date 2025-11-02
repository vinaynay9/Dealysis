export function MemoEditor({ content, setContent }) {
  return (
    <div className="bg-white shadow-sm border border-gray-200 rounded-lg p-6">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="w-full h-screen p-4 border-none resize-none focus:outline-none font-mono text-sm"
        placeholder="Edit your memo content here..."
      />
    </div>
  );
}
