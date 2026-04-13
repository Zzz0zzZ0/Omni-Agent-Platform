import React from 'react';
import { 
  User, 
  Hash, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle,
  Clock,
  ExternalLink
} from 'lucide-react';

export default function TicketCard({ ticket, currentRole, onAction }) {
  // 从 ingestion 流程中获取 OCR 的原始结果
  const ocrResults = ticket.ocr_results || [];
  const uids = [...new Set(ocrResults.map(r => r.uid).filter(Boolean))];
  const errorCodes = [...new Set(ocrResults.flatMap(r => r.error_codes).filter(Boolean))];
  
  // 假定推荐逻辑已经在后端或 Pipeline 结果中包含
  // 这里的简化逻辑是：如果该工单的推荐人不是由于当前角色，则降低不透明度（可选）
  const isRecommendedForMe = true; // 简单演示

  return (
    <div className={`glass-card rounded-2xl p-6 transition-all hover:border-primary/50 group ${!isRecommendedForMe ? 'opacity-60' : ''}`}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2">
           <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
             ticket.priority === 'P0' ? 'bg-red-500 text-white' : 'bg-blue-500/20 text-blue-400'
           }`}>
             Priority {ticket.priority || 'P2'}
           </span>
           <span className="text-xs text-gray-500 flex items-center gap-1">
             <Clock size={12} /> {new Date(ticket.timestamp).toLocaleTimeString()}
           </span>
        </div>
        <button className="text-gray-500 hover:text-white transition-colors">
          <ExternalLink size={16} />
        </button>
      </div>

      <div className="mb-4">
        <h3 className="text-sm font-semibold text-gray-200 mb-2 leading-tight">
          {ticket.raw_text_content?.substring(0, 100)}...
        </h3>
        
        {/* OCR Badges */}
        <div className="flex flex-wrap gap-2 mt-3">
          {uids.map(uid => (
            <div key={uid} className="flex items-center gap-1 px-2 py-1 bg-white/5 rounded-md text-[11px] text-gray-300 border border-white/5">
              <User size={10} className="text-primary" /> UID: {uid}
            </div>
          ))}
          {errorCodes.map(code => (
            <div key={code} className="flex items-center gap-1 px-2 py-1 bg-red-500/10 rounded-md text-[11px] text-red-400 border border-red-500/10">
              <AlertTriangle size={10} /> {code}
            </div>
          ))}
          {ticket.tags?.map(tag => (
             <div key={tag} className="flex items-center gap-1 px-2 py-1 bg-white/5 rounded-md text-[11px] text-gray-400">
               <Hash size={10} /> {tag}
             </div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between pt-4 border-t border-white/5">
        <div className="flex flex-col">
           <span className="text-[10px] text-gray-500 uppercase tracking-wider">系统推荐反馈</span>
           <span className="text-xs font-medium text-primary">建议分发至: {currentRole}</span>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => onAction(0, [], 0)} // 简化调用
            className="p-2 rounded-lg hover:bg-red-500/10 text-gray-500 hover:text-red-500 transition-all border border-transparent hover:border-red-500/20"
            title="忽略此工单"
          >
            <XCircle size={18} />
          </button>
          <button 
             onClick={() => onAction(0, [], 1)} // 简化调用
             className="flex items-center gap-2 px-4 py-2 bg-primary/10 hover:bg-primary text-primary hover:text-white rounded-lg transition-all text-xs font-bold border border-primary/20"
          >
            <CheckCircle2 size={16} /> 标记处理
          </button>
        </div>
      </div>
    </div>
  );
}
