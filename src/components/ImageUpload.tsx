"use client";

import { useRef, useState, useCallback } from "react";

interface ImageUploadProps {
  onImageSelect: (imageData: string) => void;
  currentImage: string | null;
  label: string;
  description: string;
}

export default function ImageUpload({ onImageSelect, currentImage, label, description }: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback((file: File) => {
    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const result = e.target?.result as string;
        onImageSelect(result);
      };
      reader.readAsDataURL(file);
    }
  }, [onImageSelect]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }, [handleFile]);

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-zinc-300">{label}</label>
      <div
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative cursor-pointer rounded-xl border-2 border-dashed transition-all
          ${isDragging
            ? "border-purple-500 bg-purple-500/10"
            : currentImage
              ? "border-zinc-600 bg-zinc-800/50"
              : "border-zinc-700 hover:border-zinc-500 bg-zinc-800/30"
          }
        `}
      >
        {currentImage ? (
          <div className="relative aspect-square">
            <img
              src={currentImage}
              alt="Selected"
              className="w-full h-full object-cover rounded-xl"
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onImageSelect("");
              }}
              className="absolute top-2 right-2 p-1 bg-black/60 hover:bg-black/80 rounded-full transition-colors"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ) : (
          <div className="aspect-square flex flex-col items-center justify-center p-6 text-center">
            <svg className="w-12 h-12 text-zinc-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-sm text-zinc-400">{description}</p>
            <p className="text-xs text-zinc-500 mt-1">or drag and drop</p>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={handleInputChange}
          className="hidden"
        />
      </div>
    </div>
  );
}
