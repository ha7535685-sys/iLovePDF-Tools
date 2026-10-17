"use client";

import { Header } from "@/components/Header";
import { UploadArea } from "@/components/UploadArea";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { submitAndPoll, triggerDownload } from "@/lib/apiClient";

export default function SplitPDFPage() {
  const [ranges, setRanges] = useState("1");

  const handleProcess = async (files: File[], onStatus: (msg: string) => void) => {
    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("split_mode", "fixed_ranges");
    formData.append("ranges", ranges || "1");

    const { filename, downloadUrl } = await submitAndPoll("/split", formData, onStatus);
    triggerDownload(downloadUrl, filename);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      <Header />
      <main className="flex-1 w-full max-w-3xl px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Split PDF files
        </h1>
        <p className="text-xl text-gray-500 text-center mb-12 max-w-2xl">
          Separate one page or a whole set for easy conversion into independent PDF files.
        </p>
        <div className="w-full max-w-4xl mb-6 px-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border mb-4">
            <Label htmlFor="ranges" className="text-lg font-semibold mb-2 block">Custom Page Ranges</Label>
            <p className="text-sm text-gray-500 mb-4">Enter page ranges separated by commas (e.g. 1-2, 4, 5-8)</p>
            <Input
              id="ranges"
              type="text"
              placeholder="e.g. 1-3, 5-7"
              value={ranges}
              onChange={(e) => setRanges(e.target.value)}
              className="max-w-md"
            />
          </div>
        </div>
        <UploadArea
          onProcess={handleProcess}
          title="Select PDF file"
          buttonText="Split PDF"
          accept=".pdf"
          multiple={false}
          maxFiles={1}
        />
      </main>
      <footer className="w-full bg-white border-t py-8 mt-12 text-center text-gray-500 text-sm">
        &copy; {new Date().getFullYear()} iLovePDF Tools
      </footer>
    </div>
  );
}
