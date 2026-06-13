"use client";
import { useState } from "react";
import { Upload, Check } from "lucide-react";
import Header from "@/components/Header";
import { uploadDocument } from "@/lib/api";

export default function SettingsPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);
    try {
      const res = await uploadDocument(file);
      setUploadResult(res);
    } catch (err) {
      setUploadResult({ status: "error", message: err.response?.data?.detail || err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("api_key");
      window.location.href = "/";
    }
  };

  return (
    <>
      <Header
        currentRole=""
        roles={[]}
        onRoleChange={() => {}}
        onRefresh={() => {}}
        isConnected={false}
      />
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-3xl mx-auto space-y-8 animate-fade-in">
          <h2 className="text-2xl font-bold">系统设置</h2>

          {/* 知识库上传 */}
          <section className="glass-card rounded-2xl p-6">
            <h3 className="font-bold mb-4 text-base">知识库管理</h3>
            <p className="text-sm text-[var(--text-secondary)] mb-4">
              上传 PDF 或 TXT 文件，构建 RAG 检索知识库。
            </p>

            <label className="flex items-center justify-center gap-3 p-8 border-2 border-dashed border-[var(--border)] rounded-xl cursor-pointer hover:border-[var(--accent)]/40 hover:bg-[var(--accent)]/5 transition-all">
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploading}
              />
              {uploading ? (
                <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                  <div className="w-5 h-5 border-2 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
                  上传处理中...
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                  <Upload size={20} />
                  点击上传文档 (PDF / TXT)
                </div>
              )}
            </label>

            {uploadResult && (
              <div className={`mt-4 p-4 rounded-xl text-sm ${
                uploadResult.status === "success"
                  ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                  : "bg-red-500/10 border border-red-500/20 text-red-400"
              }`}>
                {uploadResult.status === "success" ? (
                  <div className="flex items-center gap-2">
                    <Check size={16} />
                    {uploadResult.message}
                  </div>
                ) : (
                  uploadResult.message
                )}
              </div>
            )}
          </section>

          {/* 登出 */}
          <section className="glass-card rounded-2xl p-6">
            <h3 className="font-bold mb-4 text-base">账户</h3>
            <button
              onClick={handleLogout}
              className="px-6 py-2.5 bg-red-500/15 hover:bg-red-500/25 text-red-400 rounded-xl text-sm font-medium transition-colors"
            >
              退出登录
            </button>
          </section>
        </div>
      </div>
    </>
  );
}
