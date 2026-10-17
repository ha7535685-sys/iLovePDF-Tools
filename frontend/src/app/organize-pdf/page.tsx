"use client";

import { Header } from "@/components/Header";
import { UploadArea } from "@/components/UploadArea";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { submitAndPoll, triggerDownload } from "@/lib/apiClient";

export default function OrganizePDFPage() {
  const [order, setOrder] = useState("");

  const handleProcess = async (files: File[], onStatus: (msg: string) => void) => {
    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("order", order);

    const { filename, downloadUrl } = await submitAndPoll("/organize-pdf", formData, onStatus);
    triggerDownload(downloadUrl, filename);
  };

  return (
    <div className="min-h-screen bg-[#FDFBF9] flex flex-col items-center">
      <Header />
      <main className="flex-1 w-full max-w-3xl px-4 md:px-8 py-16 flex flex-col items-center">
        <h1 className="text-4xl md:text-5xl font-bold text-center text-gray-900 mb-6">
          Organize PDF
        </h1>
        <p className="text-xl text-gray-600 text-center mb-12 max-w-2xl">
          Sort pages of your PDF file however you like.
        </p>
        <div className="w-full max-w-md mb-6 px-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border mb-4">
            <Label htmlFor="order" className="text-lg font-semibold mb-2 block">New Page Order</Label>
            <p className="text-sm text-gray-500 mb-4">Enter page numbers in the new desired order, separated by commas (e.g. 3, 1, 2)</p>
            <Input
              id="order"
              type="text"
              placeholder="e.g. 3, 1, 2"
              value={order}
              onChange={(e) => setOrder(e.target.value)}
              className="w-full p-3 bg-gray-50 focus-visible:ring-primary"
            />
          </div>
        </div>
        <UploadArea
          onProcess={handleProcess}
          title="Select PDF file"
          buttonText="Organize PDF"
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
