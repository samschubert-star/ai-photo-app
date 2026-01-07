"use client";

interface ResultsDisplayProps {
  originalImage: string;
  resultImage: string | null;
  loading: boolean;
  error: string | null;
}

export default function ResultsDisplay({ originalImage, resultImage, loading, error }: ResultsDisplayProps) {
  const handleDownload = () => {
    if (!resultImage) return;

    const link = document.createElement("a");
    link.href = resultImage;
    link.download = `virtual-tryon-${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Result</h3>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <p className="text-sm text-zinc-400">Original</p>
          <div className="aspect-[3/4] rounded-xl overflow-hidden bg-zinc-800">
            <img
              src={originalImage}
              alt="Original photo"
              className="w-full h-full object-cover"
            />
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm text-zinc-400">With New Outfit</p>
          <div className="aspect-[3/4] rounded-xl overflow-hidden bg-zinc-800 relative">
            {loading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="relative">
                  <div className="w-16 h-16 border-4 border-purple-500/30 rounded-full" />
                  <div className="absolute top-0 left-0 w-16 h-16 border-4 border-transparent border-t-purple-500 rounded-full animate-spin" />
                </div>
                <p className="text-sm text-zinc-400 mt-4">Generating...</p>
                <p className="text-xs text-zinc-500 mt-1">This may take 30-60 seconds</p>
              </div>
            ) : error ? (
              <div className="absolute inset-0 flex items-center justify-center p-4">
                <div className="text-center">
                  <svg className="w-12 h-12 text-red-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              </div>
            ) : resultImage ? (
              <img
                src={resultImage}
                alt="Virtual try-on result"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-sm text-zinc-500">Result will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {resultImage && !loading && (
        <button
          onClick={handleDownload}
          className="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download Result
        </button>
      )}
    </div>
  );
}
