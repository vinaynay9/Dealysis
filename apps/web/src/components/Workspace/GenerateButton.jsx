export function GenerateButton({
  onClick,
  isProcessing,
  processingStage,
  disabled,
  generationProgress,
}) {
  return (
    <div className="text-center">
      <button
        onClick={onClick}
        disabled={isProcessing || disabled}
        className="px-8 py-4 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] hover:from-[#5B61F0] hover:to-[#7C3AED] disabled:bg-[#4B5563] text-white font-semibold text-lg rounded-2xl transition-colors focus:outline-none focus:ring-2 focus:ring-[#6366F1] focus:ring-offset-2 disabled:cursor-not-allowed min-w-[300px]"
        style={{ fontFamily: "Inter, sans-serif" }}
      >
        {isProcessing ? (
          <div className="flex flex-col items-center space-y-2">
            <div className="flex items-center space-x-3">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>{processingStage}</span>
            </div>
            {generationProgress && generationProgress.currentStep > 0 && (
              <div className="w-full">
                <div className="flex justify-between text-sm opacity-90 mb-1">
                  <span>
                    Section {generationProgress.currentStep} of{" "}
                    {generationProgress.totalSections}
                  </span>
                  <span>
                    {Math.round(
                      (generationProgress.currentStep /
                        generationProgress.totalSections) *
                        100,
                    )}
                    %
                  </span>
                </div>
                <div className="w-full bg-white/20 rounded-full h-2">
                  <div
                    className="bg-white h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${(generationProgress.currentStep / generationProgress.totalSections) * 100}%`,
                    }}
                  ></div>
                </div>
                {generationProgress.currentSection && (
                  <div className="text-sm opacity-75 mt-1">
                    {generationProgress.currentSection}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          "Generate Investment Memo"
        )}
      </button>

      {generationProgress?.error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="text-red-800 text-sm">
            <strong>Warning:</strong> {generationProgress.error}
          </div>
          <div className="text-red-600 text-xs mt-1">
            The memo will continue generating with placeholder sections for
            failed parts.
          </div>
        </div>
      )}
    </div>
  );
}
