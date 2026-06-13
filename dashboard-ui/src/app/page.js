"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { setApiKey, createTenant } from "@/lib/api";
import { LayoutDashboard, Key, Plus } from "lucide-react";

export default function LoginPage() {
  const [apiKey, setApiKeyState] = useState("");
  const [tenantName, setTenantName] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createdKey, setCreatedKey] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = () => {
    if (!apiKey.trim()) {
      setError("请输入 API Key");
      return;
    }
    setApiKey(apiKey.trim());
    if (typeof window !== "undefined") {
      localStorage.setItem("api_key", apiKey.trim());
    }
    router.push("/dashboard");
  };

  const handleCreate = async () => {
    if (!tenantName.trim()) return;
    try {
      const res = await createTenant(tenantName.trim());
      setCreatedKey(res.api_key);
      setApiKeyState(res.api_key);
      setError("");
    } catch (e) {
      setError("创建失败: " + (e.response?.data?.detail || e.message));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)]">
      <div className="glass-card rounded-3xl p-10 w-full max-w-md animate-slide-up">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[var(--accent)]/10 mb-4 animate-pulse-glow">
            <LayoutDashboard size={32} className="text-[var(--accent)]" />
          </div>
          <h1 className="text-2xl font-bold gradient-text">Omni Agent Platform</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-2">B2B 游戏运营智能体平台</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-[var(--text-secondary)] uppercase tracking-wider font-medium">
              API Key
            </label>
            <div className="relative mt-1.5">
              <Key size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-secondary)]" />
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKeyState(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                placeholder="hap_xxxxxxxxxxxxxxxx"
                className="w-full pl-10 pr-4 py-3 bg-white/5 border border-[var(--border)] rounded-xl text-sm focus:border-[var(--accent)] focus:outline-none transition-colors"
              />
            </div>
          </div>

          {error && (
            <p className="text-red-400 text-xs">{error}</p>
          )}

          <button
            onClick={handleLogin}
            className="w-full py-3 bg-[var(--accent)] hover:bg-[var(--accent)]/90 text-white rounded-xl font-semibold text-sm transition-all duration-200 hover:shadow-lg hover:shadow-[var(--accent)]/20"
          >
            登录看板
          </button>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[var(--border)]" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 bg-[var(--bg-card)] text-[var(--text-secondary)]">或</span>
            </div>
          </div>

          <button
            onClick={() => setShowCreate(!showCreate)}
            className="w-full py-3 border border-[var(--border)] hover:bg-white/5 rounded-xl text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all flex items-center justify-center gap-2"
          >
            <Plus size={14} />
            创建新租户
          </button>

          {showCreate && (
            <div className="space-y-3 animate-fade-in">
              <input
                type="text"
                value={tenantName}
                onChange={(e) => setTenantName(e.target.value)}
                placeholder="租户名称（如：XX 游戏工作室）"
                className="w-full px-4 py-3 bg-white/5 border border-[var(--border)] rounded-xl text-sm focus:border-[var(--accent)] focus:outline-none"
              />
              <button
                onClick={handleCreate}
                className="w-full py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-xl text-sm font-medium transition-colors"
              >
                创建并获取 API Key
              </button>
              {createdKey && (
                <div className="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded-xl">
                  <p className="text-[10px] text-emerald-400 uppercase font-medium mb-1">已生成 API Key（请保存）</p>
                  <code className="text-xs text-emerald-300 break-all">{createdKey}</code>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
