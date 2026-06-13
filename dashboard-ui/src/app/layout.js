import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Omni Agent Platform — 游戏运营智能看板",
  description: "B2B 级多租户游戏运营 AI 平台",
};

export default function RootLayout({ children }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
