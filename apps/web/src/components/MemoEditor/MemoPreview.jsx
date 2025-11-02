import ReactMarkdown from "react-markdown";

export function MemoPreview({ content }) {
  return (
    <div className="bg-white shadow-sm border border-gray-200 rounded-lg p-8 min-h-screen">
      <article className="prose prose-gray max-w-none">
        <ReactMarkdown
          components={{
            h1: ({ children }) => (
              <h1
                id={children.toString().toLowerCase().replace(/\s+/g, "-")}
                className="text-3xl font-bold text-gray-900 mb-6 pb-2 border-b border-gray-200"
              >
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-xl font-semibold text-gray-800 mt-6 mb-3">
                {children}
              </h3>
            ),
            p: ({ children }) => (
              <p className="text-gray-700 leading-relaxed mb-4">{children}</p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc pl-6 mb-4 space-y-2">{children}</ul>
            ),
            li: ({ children }) => <li className="text-gray-700">{children}</li>,
            strong: ({ children }) => (
              <strong className="font-semibold text-gray-900">
                {children}
              </strong>
            ),
            img: ({ src, alt }) => (
              <div className="my-6 text-center">
                <img
                  src={src}
                  alt={alt}
                  className="max-w-full h-auto rounded-lg shadow-md mx-auto"
                />
                {alt && (
                  <p className="text-sm text-gray-600 mt-2 italic">{alt}</p>
                )}
              </div>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </article>
    </div>
  );
}
