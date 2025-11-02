import { X, Quote, FileText, Link2, Type } from "lucide-react";

export function CitationModal({
  isOpen,
  onClose,
  bibliography,
  onInsertCitation,
}) {
  if (!isOpen) return null;

  const getSourceIcon = (type) => {
    switch (type) {
      case "document":
        return <FileText size={16} className="text-blue-500" />;
      case "url":
        return <Link2 size={16} className="text-green-500" />;
      case "text":
        return <Type size={16} className="text-purple-500" />;
      default:
        return <Quote size={16} className="text-gray-500" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">
            Insert Citation
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-4">
          <p className="text-sm text-gray-600 mb-4">
            Select a source to insert as an in-text citation. The citation will
            appear as [1], [2], etc.
          </p>

          {bibliography.length === 0 ? (
            <div className="text-center py-8">
              <Quote size={48} className="text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No bibliography sources available</p>
              <p className="text-sm text-gray-400 mt-2">
                Bibliography sources are automatically generated from your
                reference materials
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {bibliography.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onInsertCitation(item.id)}
                  className="w-full p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left"
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {getSourceIcon(item.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                          {item.id}
                        </span>
                        <h4 className="font-medium text-gray-900 truncate">
                          {item.title}
                        </h4>
                      </div>
                      <p className="text-sm text-gray-600 truncate">
                        {item.description}
                      </p>
                      <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                        <span>{item.source}</span>
                        <span>{item.date}</span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end space-x-3 p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
