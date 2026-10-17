"use client";

import { Header } from "@/components/Header";
import { UploadArea } from "@/components/UploadArea";
import { useState } from "react";
import { Label } from "@/components/ui/label";
import { submitAndPoll, triggerDownload } from "@/lib/apiClient";

export default function AddPageNumbersPage() {
  const [position, setPosition] = useState("bottom-right");

  const handleProcess = async (files: File[], onStatus: (msg: string) => void) => {
    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("position", position);

    const { filename, downloadUrl } = await submitAndPoll("/add-page-numbers", formData, onStatus);
    triggerDownload(downloadUrl, filename);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      <Header />
      <main className="flex-1 w-full max-w-3xl px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Add Page Numbers
        </h1>
        <p className="text-xl text-gray-500 text-center mb-12 max-w-2xl">
          Add page numbers into PDFs with ease. Choose your positions, dimensions, typography.
        </p>
        <div className="w-full max-w-md mb-6 px-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border mb-4">
            <Label htmlFor="position" className="text-lg font-semibold mb-2 block">Position</Label>
            <select
              id="position"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="w-full border rounded-md p-2 mt-2 bg-white"
            >
              <option value="bottom-right">Bottom Right</option>
              <option value="bottom-center">Bottom Center</option>
              <option value="bottom-left">Bottom Left</option>
              <option value="top-right">Top Right</option>
              <option value="top-center">Top Center</option>
              <option value="top-left">Top Left</option>
            </select>
          </div>
        </div>
        <UploadArea
          onProcess={handleProcess}
          title="Select PDF file"
          buttonText="Add Page Numbers"
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
