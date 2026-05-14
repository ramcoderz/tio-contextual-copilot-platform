import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useChatStore } from "../store";
import { api } from "../api";
import { 
  Plus, Bot, Globe, Calendar, ArrowRight, Activity, 
  ExternalLink, Search, Filter, MoreVertical 
} from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const [chatbots, setChatbots] = useState([]);
  const [loading, setLoading] = useState(true);
  const { setChatbotId } = useChatStore();

  useEffect(() => {
    api("/chatbots").then(data => {
      setChatbots(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="page-container" style={{ maxWidth: '1100px', margin: '0 auto', padding: '40px 24px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '48px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '8px' }}>
            Your Intelligence <span className="text-gradient">Fleet</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '16px' }}>
            Manage and monitor your context-aware chatbots.
          </p>
        </div>
        <Link to="/create" className="btn btn-primary" style={{ padding: '12px 24px' }}>
          <Plus size={18} /> Create New Copilot
        </Link>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '24px' }}>
        {loading ? (
          [1, 2, 3].map(i => (
            <div key={i} className="glass-panel" style={{ height: '200px', opacity: 0.5 }}></div>
          ))
        ) : chatbots.length === 0 ? (
          <div className="glass-panel" style={{ gridColumn: '1/-1', textAlign: 'center', padding: '80px 40px' }}>
             <Bot size={48} style={{ margin: '0 auto 24px', opacity: 0.2 }} />
             <h3 style={{ fontSize: '20px', fontWeight: 600, marginBottom: '8px' }}>No Chatbots Found</h3>
             <p style={{ color: 'var(--text-dim)', marginBottom: '24px' }}>Start by connecting a website or uploading documents.</p>
             <Link to="/create" className="btn btn-secondary">Get Started</Link>
          </div>
        ) : chatbots.map((bot, i) => (
          <motion.div 
            key={bot.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-panel chatbot-card"
            style={{ padding: '24px', cursor: 'pointer', position: 'relative', overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div style={{ 
                width: '44px', height: '44px', borderRadius: '12px', background: 'var(--accent-glow)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)'
              }}>
                <Bot size={24} />
              </div>
              <div style={{ 
                padding: '4px 10px', borderRadius: '20px', background: bot.status === 'ready' ? 'rgba(34,197,94,0.1)' : 'rgba(234,179,8,0.1)',
                color: bot.status === 'ready' ? '#4ade80' : '#facc15', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', height: 'fit-content'
              }}>
                {bot.status}
              </div>
            </div>

            <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>{bot.name}</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '20px' }}>
              <Globe size={14} /> {bot.website_url ? new URL(bot.website_url).hostname : "Manual Documents"}
            </p>

            <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
              <Link 
                to="/chat" 
                onClick={() => setChatbotId(bot.id)}
                className="btn btn-sm btn-primary" 
                style={{ flex: 1 }}
              >
                Chat <ArrowRight size={14} />
              </Link>
              <Link to={`/chatbots/${bot.id}`} className="btn btn-sm btn-ghost" style={{ padding: '0 12px' }}>
                <Settings size={16} />
              </Link>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
