"use client";

import { useState, useCallback } from "react";
import CameraCapture from "@/components/CameraCapture";
import ImageUpload from "@/components/ImageUpload";
import ClothingUrlInput from "@/components/ClothingUrlInput";
import ResultsDisplay from "@/components/ResultsDisplay";

type Step = "upload" | "processing" | "result";

export default function Home() {
  const [step, setStep] = useState<Step>("upload");
  const [showCamera, setShowCamera] = useState(false);
  const [personImage, setPersonImage] = useState<string | null>(null);
  const [clothingUrl, setClothingUrl] = useState("");
  const [clothingImage, setClothingImage] = useState<string | null>(null);
  const [resultImage, setResultImage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCameraCapture = useCallback((imageData: string) => {
    setPersonImage(imageData);
    setShowCamera(false);
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!personImage || !clothingImage) return;

    setStep("processing");
    setLoading(true);
    setError(null);
    setResultImage(null);

    try {
      const response = await fetch("/api/try-on", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          personImage,
          clothingImage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate image");
      }

      setResultImage(data.resultImage);
      setStep("result");

      if (data.demo) {
        setError("Demo mode: Configure REPLICATE_API_TOKEN for real AI processing");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setStep("result");
    } finally {
      setLoading(false);
    }
  }, [personImage, clothingImage]);

  const handleReset = useCallback(() => {
    setStep("upload");
    setPersonImage(null);
    setClothingUrl("");
    setClothingImage(null);
    setResultImage(null);
    setError(null);
  }, []);

  const handleTryAnother = useCallback(() => {
    setStep("upload");
    setClothingUrl("");
    setClothingImage(null);
    setResultImage(null);
    setError(null);
  }, []);

  const canGenerate = personImage && clothingImage;

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-900 to-purple-900/20">
      {/* Header */}
      <header className="border-b border-zinc-800 bg-zinc-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Virtual Try-On</h1>
              <p className="text-xs text-zinc-400">AI-Powered Outfit Preview</p>
            </div>
          </div>
          {(step === "result" || step === "processing") && (
            <button
              onClick={handleReset}
              className="text-sm text-zinc-400 hover:text-white transition-colors"
            >
              Start Over
            </button>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {step === "upload" && (
          <div className="space-y-8">
            {/* Instructions */}
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-white">
                See How Any Outfit Looks On You
              </h2>
              <p className="text-zinc-400 max-w-md mx-auto">
                Take a photo of yourself, paste a link to any clothing item, and let AI show you the look.
              </p>
            </div>

            {/* Upload Section */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Person Photo */}
              <div className="space-y-4">
                <ImageUpload
                  onImageSelect={setPersonImage}
                  currentImage={personImage}
                  label="Your Photo"
                  description="Click to upload or take a photo"
                />
                {!personImage && (
                  <button
                    onClick={() => setShowCamera(true)}
                    className="w-full py-3 border border-zinc-700 hover:border-zinc-500 rounded-xl text-zinc-300 hover:text-white transition-colors flex items-center justify-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Use Camera
                  </button>
                )}
              </div>

              {/* Clothing URL */}
              <div className="space-y-4">
                <ClothingUrlInput
                  onUrlSubmit={setClothingUrl}
                  onImageLoad={setClothingImage}
                  currentUrl={clothingUrl}
                  clothingImage={clothingImage}
                />
                <div className="text-center">
                  <span className="text-xs text-zinc-500">or upload directly</span>
                </div>
                <ImageUpload
                  onImageSelect={setClothingImage}
                  currentImage={null}
                  label=""
                  description="Upload clothing image"
                />
              </div>
            </div>

            {/* Generate Button */}
            <div className="pt-4">
              <button
                onClick={handleGenerate}
                disabled={!canGenerate}
                className={`
                  w-full py-4 rounded-xl font-semibold text-lg transition-all
                  ${canGenerate
                    ? "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg shadow-purple-500/25"
                    : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                  }
                `}
              >
                {canGenerate ? "Generate Try-On" : "Add Photo & Clothing to Continue"}
              </button>
            </div>

            {/* Tips */}
            <div className="bg-zinc-800/50 rounded-xl p-4 space-y-3">
              <h3 className="font-medium text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                Tips for Best Results
              </h3>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• Use a front-facing photo with good lighting</li>
                <li>• Stand straight with arms slightly away from body</li>
                <li>• Use clothing images with white or plain backgrounds</li>
                <li>• Full-body photos work best for pants/dresses</li>
              </ul>
            </div>
          </div>
        )}

        {(step === "processing" || step === "result") && personImage && (
          <div className="space-y-6">
            <ResultsDisplay
              originalImage={personImage}
              resultImage={resultImage}
              loading={loading}
              error={error}
            />

            {step === "result" && resultImage && (
              <div className="flex gap-4">
                <button
                  onClick={handleTryAnother}
                  className="flex-1 py-3 border border-zinc-700 hover:border-zinc-500 rounded-xl text-zinc-300 hover:text-white transition-colors"
                >
                  Try Different Clothing
                </button>
                <button
                  onClick={handleReset}
                  className="flex-1 py-3 border border-zinc-700 hover:border-zinc-500 rounded-xl text-zinc-300 hover:text-white transition-colors"
                >
                  New Photo
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Camera Modal */}
      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-zinc-800 mt-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center text-sm text-zinc-500">
          <p>Powered by AI. Results are for visualization purposes only.</p>
        </div>
      </footer>
    </div>
  );
}
