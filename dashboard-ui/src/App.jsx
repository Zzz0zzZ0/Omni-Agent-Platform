import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  MessageSquare, 
  History, 
  AlertCircle, 
  Settings, 
  UserCircle,
  TrendingDown,
  TrendingUp,
  LayoutDashboard,
  Bell
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import TicketCard from './components/TicketCard';

const API_BASE = "http://localhost:8000/api/v1";

function App() {
  const [activeTab, setActiveTab] = useState('pipeline');
  const [currentRole, setCurrentRole] = useState('Comm_Specialist');
  const [summary, setSummary] = useState('');
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);

  const roles = [
    { id: 'Comm_Specialist', label: '商业化运营', color: 'text-emerald-400' },
    { id: 'PR_Specialist', label: '公关舆情员', color: 'text-amber-400' },
    { id: 'Content_Planner', label: '活动策划', color: 'text-sky-400' },
    { id: 'Tech_Support', label: '技术维护', color: 'text-purple-400' }
  ];

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [sumRes, tickRes] = await Promise.all([
        axios.get(`${API_BASE}/dashboard/summary`),
        axios.get(`${API_BASE}/dashboard/tickets`)
      ]);
      setSummary(sumRes.data.markdown);
      setTickets(tickRes.data.tickets);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (armIdx, contextVec, reward) => {
    try {
      await axios.post(`${API_BASE}/recommendation/reward`, {
        arm_idx: armIdx,
        context_vec: contextVec,
        reward: reward
      });
      alert(reward === 1 ? "工单已标记处理，模型已更新" : "已忽略，模型已学习偏好");
      fetchDashboardData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <LayoutDashboard className="text-primary" />
            Honkai Agent
          </h1>
        </div>
        
        <nav className="flex-1 space-y-1 px-4 mt-4">
          <button 
            onClick={() => setActiveTab('monitor')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'monitor' ? 'sidebar-item-active' : 'hover:bg-white/5'}`}
          >
            <BarChart3 size={20} /> 舆情监控台
          </button>
          <button 
            onClick={() => setActiveTab('pipeline')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'pipeline' ? 'sidebar-item-active' : 'hover:bg-white/5'}`}
          >
            <MessageSquare size={20} /> 待处理流水线
          </button>
          <button 
            onClick={() => setActiveTab('history')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${activeTab === 'history' ? 'sidebar-item-active' : 'hover:bg-white/5'}`}
          >
            <History size={20} /> 历史工单库
          </button>
        </nav>

        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 px-2 py-2">
            <UserCircle size={28} className="text-gray-400" />
            <div className="text-xs">
              <p className="font-semibold text-gray-200">Admin User</p>
              <p className="text-gray-500">System Operator</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header */}
        <header className="h-20 border-b border-border flex items-center justify-between px-8 bg-background/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-8">
            <div className="text-sm">
              <span className="text-gray-500">当前视图:</span>
              <select 
                value={currentRole}
                onChange={(e) => setCurrentRole(e.target.value)}
                className="ml-2 bg-transparent border-none font-bold text-primary focus:ring-0 cursor-pointer"
              >
                {roles.map(r => (
                  <option key={r.id} value={r.id} className="bg-card">{r.label}</option>
                ))}
              </select>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="flex gap-4">
               <div className="px-3 py-1 bg-red-500/10 border border-red-500/20 text-red-500 rounded-full text-xs font-bold flex items-center gap-1">
                 <AlertCircle size={14} /> 3 P0 告警
               </div>
               <div className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-500 rounded-full text-xs font-bold flex items-center gap-1">
                 <Bell size={14} /> 12 新反馈
               </div>
            </div>
          </div>
          <button onClick={fetchDashboardData} className="p-2 hover:bg-white/5 rounded-full text-gray-400">
             刷新大盘
          </button>
        </header>

        {/* Board Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            
            {/* Tab: Pipeline (Recommended Tickets) */}
            {activeTab === 'pipeline' && (
              <div className="grid grid-cols-12 gap-8 animate-in fade-in duration-500">
                {/* Left: Summary Analysis */}
                <div className="col-span-4 space-y-6">
                  <section className="glass-card rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-bold flex items-center gap-2">
                          <TrendingUp size={20} className="text-amber-400" />
                          今日社区核心矛盾
                        </h2>
                    </div>
                    <div className="prose prose-invert prose-sm max-w-none text-gray-300 leading-relaxed">
                       <ReactMarkdown>{summary}</ReactMarkdown>
                    </div>
                  </section>

                  <section className="glass-card rounded-2xl p-6 border-l-4 border-primary">
                    <h3 className="font-bold mb-2 text-sm">LinUCB 推荐引擎</h3>
                    <p className="text-xs text-gray-500 leading-relaxed">
                      当前对 <b>{roles.find(r => r.id === currentRole)?.label}</b> 的分发权重已根据历史行为完成深度校准。
                    </p>
                  </section>
                </div>

                {/* Right: Personalized Ticket Feed */}
                <div className="col-span-8">
                  <div className="flex items-center justify-between mb-4">
                      <h2 className="text-xl font-bold">待处理推荐流</h2>
                      <span className="text-[10px] px-2 py-1 bg-white/5 rounded text-gray-500">基于 LCB 置信区间算法</span>
                  </div>
                  
                  <div className="space-y-4">
                      {loading ? (
                        <div className="text-center py-20 text-gray-600">加载反馈流水线中...</div>
                      ) : tickets.length > 0 ? (
                        tickets.map(ticket => (
                          <TicketCard 
                            key={ticket.event_id} 
                            ticket={ticket} 
                            currentRole={currentRole}
                            onAction={handleAction}
                          />
                        ))
                      ) : (
                        <div className="text-center py-20 text-gray-600 glass-card rounded-2xl border-dashed border-white/5">
                          暂无待处理工单，系统正在持续感知中
                        </div>
                      )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Monitor (輿情大盘) */}
            {activeTab === 'monitor' && (
              <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold">全服舆情动态监控</h2>
                  <div className="flex gap-2">
                    <span className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-xs rounded-full border border-emerald-500/20">系统健康度: 98%</span>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-6">
                   <div className="glass-card p-6 rounded-2xl">
                     <p className="text-gray-500 text-xs uppercase mb-1">今日处理总量</p>
                     <p className="text-3xl font-bold">1,284</p>
                     <p className="text-emerald-500 text-xs mt-2 flex items-center gap-1">↑ 12.5% vs 昨日</p>
                   </div>
                   <div className="glass-card p-6 rounded-2xl">
                     <p className="text-gray-500 text-xs uppercase mb-1">平均响应时长</p>
                     <p className="text-3xl font-bold">4.2m</p>
                     <p className="text-emerald-500 text-xs mt-2 flex items-center gap-1">↓ 0.8m vs 上周</p>
                   </div>
                   <div className="glass-card p-6 rounded-2xl">
                     <p className="text-gray-500 text-xs uppercase mb-1">冲突密集度</p>
                     <p className="text-3xl font-bold">Medium</p>
                     <p className="text-amber-500 text-xs mt-2">受卡池保底机制影响波动</p>
                   </div>
                </div>

                <div className="glass-card p-8 rounded-2xl">
                   <h3 className="font-bold mb-6 flex items-center gap-2">
                     <Bell size={18} className="text-primary" /> 
                     实时冲突热力摘要
                   </h3>
                   <div className="prose prose-invert max-w-none">
                     <ReactMarkdown>{summary}</ReactMarkdown>
                   </div>
                </div>
              </div>
            )}

            {/* Tab: History (历史工单) */}
            {activeTab === 'history' && (
              <div className="animate-in fade-in duration-500">
                <div className="mb-8">
                  <h2 className="text-2xl font-bold">历史处理库</h2>
                  <p className="text-gray-500 text-sm">归档的已处理工单与算法反馈记录</p>
                </div>
                <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
                   <table className="w-full text-left text-sm">
                     <thead className="bg-white/5 text-gray-400">
                        <tr>
                          <th className="p-4 font-semibold uppercase text-[10px]">时间</th>
                          <th className="p-4 font-semibold uppercase text-[10px]">内容摘要</th>
                          <th className="p-4 font-semibold uppercase text-[10px]">处理人评分</th>
                          <th className="p-4 font-semibold uppercase text-[10px]">状态</th>
                        </tr>
                     </thead>
                     <tbody className="divide-y divide-white/5">
                        <tr className="hover:bg-white/5 transition-colors">
                          <td className="p-4 text-gray-500">2026-04-13 14:20</td>
                          <td className="p-4">充值未到帐 UID 10086...</td>
                          <td className="p-4"><span className="text-emerald-400">+1.0 (Useful)</span></td>
                          <td className="p-4"><span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-500 rounded text-[10px]">已归档</span></td>
                        </tr>
                        <tr className="hover:bg-white/5 transition-colors opacity-50">
                          <td className="p-4 text-gray-500">2026-04-13 12:10</td>
                          <td className="p-4">为什么不出黄泉专武？...</td>
                          <td className="p-4"><span className="text-red-400">0.0 (Ignored)</span></td>
                          <td className="p-4"><span className="px-2 py-0.5 bg-gray-500/10 text-gray-500 rounded text-[10px]">已略过</span></td>
                        </tr>
                     </tbody>
                   </table>
                </div>
              </div>
            )}

          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
