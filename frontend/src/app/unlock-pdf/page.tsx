"use client";

import { Header } from "@/components/Header";
import { UploadArea } from "@/components/UploadArea";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { submitAndPoll, triggerDownload } from "@/lib/apiClient";

export default function UnlockPDFPage() {
  const [password, setPassword] = useState("");

  const handleProcess = async (files: File[], onStatus: (msg: string) => void) => {
    if (!password) throw new Error("Please enter the password to unlock the PDF.");

    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("password", password);

    const { filename, downloadUrl } = await submitAndPoll("/unlock-pdf", formData, onStatus);
    triggerDownload(downloadUrl, filename);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      <Header />
      <main className="flex-1 w-full max-w-3xl px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Unlock PDF
        </h1>
        <p className="text-xl text-gray-500 text-center mb-12 max-w-2xl">
          Remove PDF password security, giving you the freedom to use your PDFs as you want.
        </p>
        <div className="w-full max-w-md mb-6 px-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border mb-4">
            <Label htmlFor="password" className="text-lg font-semibold mb-2 block">Enter Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter password..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full"
            />
          </div>
        </div>
        <UploadArea
          onProcess={handleProcess}
          title="Select PDF file"
          buttonText="Unlock PDF"
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
