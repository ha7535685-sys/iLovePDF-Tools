"use client";

import React, { useCallback, useState } from "react";
import { Upload, File, X, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProgressBar } from "@/components/ProgressBar";

interface UploadAreaProps {
  onProcess: (files: File[], onStatus: (msg: string) => void) => Promise<void>;
  accept?: string;
  multiple?: boolean;
  title?: string;
  buttonText?: string;
  maxFiles?: number;
}

type Stage = "idle" | "processing" | "done" | "error";

export function UploadArea({
  onProcess,
  accept = ".pdf",
  multiple = true,
  title = "Select PDF files",
  buttonText = "Merge PDF",
  maxFiles = 50,
}: UploadAreaProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [stage, setStage] = useState<Stage>("idle");
  const [statusMsg, setStatusMsg] = useState("Processing your files…");
  const [errorMsg, setErrorMsg] = useState("");

  const isProcessing = stage === "processing";

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFiles = Array.from(e.dataTransfer.files).filter((file) =>
        accept.includes(file.name.substring(file.name.lastIndexOf(".")).toLowerCase())
      );
      setFiles((prev) => [...prev, ...droppedFiles].slice(0, maxFiles));
    },
    [accept, maxFiles]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const selectedFiles = Array.from(e.target.files);
        setFiles((prev) => [...prev, ...selectedFiles].slice(0, maxFiles));
      }
    },
    [maxFiles]
  );

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleProcess = async () => {
    if (files.length === 0) return;
    setStage("processing");
    setStatusMsg("Uploading file…");
    setErrorMsg("");

    try {
      await onProcess(files, (msg) => setStatusMsg(msg));
      setStage("done");
    } catch (error: unknown) {
      const msg = error instanceof Error ? error.message : "Error processing files";
      setErrorMsg(msg);
      setStage("error");
    }
  };

  const handleReset = () => {
    setFiles([]);
    setStage("idle");
    setStatusMsg("Processing your files…");
    setErrorMsg("");
  };

  // ── Overlay shown while processing / done / error ──────────────────────────
  const Overlay = () => (
    <div className="absolute inset-0 bg-white/90 z-20 flex flex-col items-center justify-center rounded-lg backdrop-blur-sm gap-4 p-8">
      {stage === "processing" && (
        <>
          <ProgressBar statusMsg={statusMsg} />
          <p className="text-gray-500 text-center text-sm max-w-xs mt-2">
            Hang tight — the server is working on your file. This may take a moment for large documents.
          </p>
          {/* Animated progress steps */}
          <div className="flex items-center gap-2 mt-2">
            {["Uploading", "Processing", "Downloading"].map((step, i) => {
              const stepStatus =
                statusMsg.toLowerCase().includes("upload") && i === 0 ? "active" :
                statusMsg.toLowerCase().includes("process") && i === 1 ? "active" :
                statusMsg.toLowerCase().includes("download") || statusMsg.toLowerCase().includes("ready") && i === 2 ? "active" : "pending";
              const done =
                (statusMsg.toLowerCase().includes("process") && i === 0) ||
                ((statusMsg.toLowerCase().includes("download") || statusMsg.toLowerCase().includes("ready")) && i <= 1);
              return (
                <React.Fragment key={step}>
                  <div className="flex flex-col items-center gap-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                      done ? "bg-primary border-primary text-white" :
                      stepStatus === "active" ? "border-primary text-primary animate-pulse" :
                      "border-gray-200 text-gray-300"
                    }`}>
                      {done ? "✓" : i + 1}
                    </div>
                    <span className={`text-[10px] font-medium ${stepStatus === "active" || done ? "text-primary" : "text-gray-300"}`}>
                      {step}
                    </span>
                  </div>
                  {i < 2 && <div className={`w-8 h-0.5 mb-4 transition-all ${done ? "bg-primary" : "bg-gray-200"}`} />}
                </React.Fragment>
              );
            })}
          </div>
        </>
      )}

      {stage === "done" && (
        <>
          <CheckCircle2 className="w-16 h-16 text-green-500" />
          <p className="text-2xl font-bold text-gray-800">Done! File downloaded.</p>
          <p className="text-sm font-medium text-green-600 bg-green-50 px-3 py-1 rounded-full">{statusMsg}</p>
          <Button onClick={handleReset} className="mt-2 rounded-full px-8">
            Process another file
          </Button>
        </>
      )}

      {stage === "error" && (
        <>
          <AlertCircle className="w-16 h-16 text-red-500" />
          <p className="text-xl font-bold text-gray-800 text-center">Something went wrong</p>
          <p className="text-red-500 text-sm text-center max-w-sm">{errorMsg}</p>
          <Button onClick={handleReset} variant="outline" className="mt-2 rounded-full px-8">
            Try again
          </Button>
        </>
      )}
    </div>
  );

  return (
    <div className="w-full max-w-4xl mx-auto p-2 sm:p-4 flex flex-col items-center">
      {files.length === 0 ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`w-full min-h-[300px] sm:min-h-[400px] md:min-h-[500px] rounded-xl flex flex-col items-center justify-center transition-all duration-300 relative overflow-hidden ${
            isDragging
              ? "bg-primary/10 border-4 border-dashed border-primary scale-[1.02]"
              : "bg-[#F3F0EC] hover:bg-[#EAE6DF]"
          }`}
        >
          <label className="flex flex-col items-center justify-center cursor-pointer w-full h-full p-4 sm:p-8 relative z-10">
            <span className="bg-primary text-white text-xl sm:text-2xl md:text-4xl font-bold py-3 sm:py-4 md:py-6 px-4 sm:px-6 md:px-12 rounded-xl shadow-lg shadow-primary/40 hover:shadow-xl hover:shadow-primary/60 hover:-translate-y-1 transition-all flex flex-col md:flex-row items-center gap-3 sm:gap-4 text-center break-words max-w-full">
              {title}
            </span>
            <span className="text-gray-600 mt-4 sm:mt-6 text-lg sm:text-xl font-medium">or drop files here</span>
            <input
              type="file"
              className="hidden"
              accept={accept}
              multiple={multiple}
              onChange={handleFileInput}
            />
          </label>
        </div>
      ) : (
        <div className="w-full bg-white rounded-xl shadow-sm border p-4 sm:p-6 min-h-[300px] sm:min-h-[400px] flex flex-col relative">
          {/* Overlay for processing/done/error states */}
          {stage !== "idle" && <Overlay />}

          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <h2 className="text-lg sm:text-xl font-bold text-gray-800">Files ready ({files.length})</h2>
            <label className="bg-gray-100 text-gray-700 hover:bg-gray-200 px-4 py-2 rounded-md cursor-pointer text-sm font-medium transition-colors w-full sm:w-auto text-center">
              <Upload size={16} className="inline mr-2" />
              Add more files
              <input
                type="file"
                className="hidden"
                accept={accept}
                multiple={multiple}
                onChange={handleFileInput}
              />
            </label>
          </div>

          <div className="flex-1 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 sm:gap-4 overflow-y-auto content-start">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="relative bg-gray-50 border rounded-lg p-2 sm:p-3 flex flex-col items-center justify-center aspect-[3/4] group hover:border-primary/50 transition-colors"
              >
                <button
                  onClick={() => removeFile(index)}
                  disabled={isProcessing}
                  className="absolute top-1 right-1 sm:top-2 sm:right-2 bg-white rounded-full p-1 shadow-sm opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity hover:bg-red-50 text-red-500 disabled:opacity-0"
                >
                  <X size={14} className="sm:w-4 sm:h-4" />
                </button>
                <File className="w-8 h-8 sm:w-12 sm:h-12 text-primary/70 mb-1 sm:mb-2" />
                <span className="text-[10px] sm:text-xs text-center text-gray-600 truncate w-full px-1 sm:px-2" title={file.name}>
                  {file.name}
                </span>
                <span className="text-[9px] sm:text-[10px] text-gray-400 mt-1">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </span>
              </div>
            ))}
          </div>

          <div className="mt-6 sm:mt-8 flex justify-center border-t pt-4 sm:pt-6">
            <Button
              size="lg"
              className="text-lg sm:text-xl px-8 sm:px-12 py-6 sm:py-8 rounded-full shadow-lg w-full sm:w-auto"
              onClick={handleProcess}
              disabled={isProcessing || (files.length < 2 && buttonText === "Merge PDF")}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 sm:h-6 sm:w-6 animate-spin" />
                  {statusMsg}
                </>
              ) : (
                buttonText
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
