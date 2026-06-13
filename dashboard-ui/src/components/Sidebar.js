"use client";
import { LayoutDashboard, BarChart3, MessageSquare, History, Settings, UserCircle } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "舆情监控台", icon: BarChart3 },
  { href: "/dashboard/pipeline", label: "待处理流水线", icon: MessageSquare },
  { href: "/dashboard/history", label: "历史工单库", icon: History },
  { href: "/dashboard/settings", label: "系统设置", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-[var(--border)] bg-[var(--bg-card)] flex flex-col">
      <div className="p-6">
        <Link href="/dashboard" className="text-xl font-bold flex items-center gap-2">
          <LayoutDashboard className="text-[var(--accent)]" size={24} />
          <span className="gradient-text">Omni Agent</span>
        </Link>
        <p className="text-[10px] text-[var(--text-secondary)] mt-1 tracking-wider uppercase">
          Game Ops Intelligence
        </p>
      </div>

      <nav className="flex-1 space-y-1 px-4 mt-2">
        {navItems.map(({ href, label, icon: Icon }) => {
          const isActive = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 text-sm ${
                isActive
                  ? "sidebar-item-active"
                  : "text-[var(--text-secondary)] hover:bg-white/5 hover:text-[var(--text-primary)]"
              }`}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-3 px-2 py-2">
          <UserCircle size={28} className="text-[var(--text-secondary)]" />
          <div className="text-xs">
            <p className="font-semibold text-[var(--text-primary)]">Admin User</p>
            <p className="text-[var(--text-secondary)]">System Operator</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
