"use client";

import { useState, useCallback } from "react";

interface ClothingUrlInputProps {
  onUrlSubmit: (url: string) => void;
  onImageLoad: (imageData: string) => void;
  currentUrl: string;
  clothingImage: string | null;
}

export default function ClothingUrlInput({ onUrlSubmit, onImageLoad, currentUrl, clothingImage }: ClothingUrlInputProps) {
  const [url, setUrl] = useState(currentUrl);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async () => {
    if (!url.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // Test if it's a valid image URL by loading it
      const response = await fetch("/api/fetch-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch image");
      }

      const data = await response.json();
      onUrlSubmit(url.trim());
      onImageLoad(data.imageData);
    } catch {
      setError("Could not load image from URL. Please check the link.");
    } finally {
      setLoading(false);
    }
  }, [url, onUrlSubmit, onImageLoad]);

  const handleClear = useCallback(() => {
    setUrl("");
    setError(null);
    onUrlSubmit("");
    onImageLoad("");
  }, [onUrlSubmit, onImageLoad]);

  return (
    <div className="space-y-3">
      <label className="block text-sm font-medium text-zinc-300">
        Clothing URL
      </label>

      {clothingImage ? (
        <div className="relative aspect-square rounded-xl overflow-hidden bg-zinc-800">
          <img
            src={clothingImage}
            alt="Clothing item"
            className="w-full h-full object-cover"
          />
          <button
            onClick={handleClear}
            className="absolute top-2 right-2 p-1 bg-black/60 hover:bg-black/80 rounded-full transition-colors"
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ) : (
        <>
          <div className="flex gap-2">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              placeholder="https://example.com/clothing-image.jpg"
              className="flex-1 px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-xl text-white placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <button
              onClick={handleSubmit}
              disabled={!url.trim() || loading}
              className="px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-xl font-medium transition-colors"
            >
              {loading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                "Load"
              )}
            </button>
          </div>

          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}

          <p className="text-xs text-zinc-500">
            Paste a link to a clothing item image (shirt, dress, jacket, etc.)
          </p>
        </>
      )}
    </div>
  );
}
