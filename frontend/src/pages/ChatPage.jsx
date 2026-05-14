import { useState, useEffect } from "react";
import { useChatStore } from "../store";
import { api } from "../api";
import { 
  Send, Bot, User, Loader2, Sparkles, AlertCircle, ChevronDown, 
  Settings, Trash2, Maximize2, Minimize2, ExternalLink
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import SkillsMenu from "../components/SkillsMenu";

export default function ChatPage() {
  const { history, addMessage, updateLastMessage, isLoading, isStreaming, setLoading, setStreaming, chatbotId, sessionId } = useChatStore();
  const [input, setInput] = useState("");
  const [showSkills, setShowSkills] = useState(false);
  const [currentChatbot, setCurrentChatbot] = useState(null);

  useEffect(() => {
    if (chatbotId) {
      api(`/chatbots/${chatbotId}`).then(setCurrentChatbot);
    }
  }, [chatbotId]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = input.trim();
    setInput("");
    addMessage({ role: "user", content: userMsg });
    setLoading(true);

    try {
      const response = await api("/chat", {
        method: "POST",
        body: JSON.stringify({
          query: userMsg,
          chatbot_id: chatbotId,
          session_id: sessionId,
          history: history.slice(-5)
        })
      });

      addMessage({ 
        role: "assistant", 
        content: response.answer,
        citations: response.citations,
        confidence: response.confidence
      });
    } catch (error) {
      addMessage({ role: "assistant", content: "Sorry, I encountered an error. Please try again." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)', padding: 0 }}>
      {/* Header */}
      <header style={{ 
        padding: '16px 24px', background: 'var(--bg-card)', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ 
            width: '36px', height: '36px', borderRadius: '10px', background: 'var(--accent-glow)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)'
          }}>
            <Bot size={20} />
          </div>
          <div>
            <h2 style={{ fontSize: '15px', fontWeight: 700 }}>{currentChatbot?.name || "TiO Copilot"}</h2>
            <p style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {currentChatbot?.domain || "General Intelligence"} • Context-Aware
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
           <button className="btn-icon"><Settings size={18} /></button>
           <button className="btn-icon"><Trash2 size={18} /></button>
        </div>
      </header>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {history.length === 0 && (
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-dim)' }}
            >
              <Bot size={48} style={{ margin: '0 auto 20px', opacity: 0.2 }} />
              <h3 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
                Start a Contextual Conversation
              </h3>
              <p style={{ maxWidth: '400px', margin: '0 auto', fontSize: '14px' }}>
                Ask me anything about {currentChatbot?.name || "this site"}. I've synthesized the content and am ready to assist.
              </p>
            </motion.div>
          )}
          {history.map((msg, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ 
                display: 'flex', gap: '16px', 
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
              }}
            >
              <div style={{ 
                width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-card)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: msg.role === 'user' ? 'white' : 'var(--accent)',
                border: msg.role === 'assistant' ? '1px solid var(--border)' : 'none'
              }}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div style={{ 
                maxWidth: '80%', 
                padding: '12px 16px',
                borderRadius: '16px',
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--bg-card)',
                color: msg.role === 'user' ? 'white' : 'var(--text-primary)',
                border: msg.role === 'assistant' ? '1px solid var(--border)' : 'none',
                boxShadow: msg.role === 'assistant' ? 'var(--shadow-sm)' : 'none',
                fontSize: '14px', lineHeight: 1.6
              }}>
                {msg.content}
                
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-light)', fontSize: '11px' }}>
                    <p style={{ fontWeight: 700, marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)' }}>Sources</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {msg.citations.map((c, j) => (
                        <div key={j} style={{ background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--border-light)' }}>
                          {c.document}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
          {isLoading && (
            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ 
                width: '32px', height: '32px', borderRadius: '8px', 
                background: 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--accent)', border: '1px solid var(--border)'
              }}>
                <Loader2 size={16} className="animate-spin" />
              </div>
              <div style={{ 
                padding: '12px 16px', borderRadius: '16px', background: 'var(--bg-card)', 
                border: '1px solid var(--border)', display: 'flex', gap: '4px'
              }}>
                <span className="dot-pulse"></span>
                <span className="dot-pulse"></span>
                <span className="dot-pulse"></span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer / Input */}
      <footer style={{ padding: '24px', background: 'transparent' }}>
        <div style={{ maxWidth: '800px', margin: '0 auto', position: 'relative' }}>
          <AnimatePresence>
            {showSkills && (
              <SkillsMenu 
                domain={currentChatbot?.domain} 
                onSelect={(skill) => { setInput(`/${skill} `); setShowSkills(false); }}
                onClose={() => setShowSkills(false)}
              />
            )}
          </AnimatePresence>
          
          <form onSubmit={handleSend} className="glass-panel" style={{ 
            display: 'flex', alignItems: 'center', padding: '8px 12px', gap: '12px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)', borderRadius: '20px'
          }}>
            <button 
              type="button"
              onClick={() => setShowSkills(!showSkills)}
              style={{ 
                width: '36px', height: '36px', borderRadius: '50%', background: 'var(--accent-glow)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)',
                transition: 'transform 0.2s'
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              <Sparkles size={18} />
            </button>
            <input 
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question or type / for skills..."
              style={{ flex: 1, background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', fontSize: '15px' }}
            />
            <button 
              type="submit"
              disabled={!input.trim() || isLoading}
              style={{ 
                width: '36px', height: '36px', borderRadius: '50%', background: 'var(--accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white',
                opacity: input.trim() ? 1 : 0.4, cursor: input.trim() ? 'pointer' : 'default'
              }}
            >
              <Send size={18} />
            </button>
          </form>
          <p style={{ textAlign: 'center', fontSize: '10px', color: 'var(--text-dim)', marginTop: '12px', letterSpacing: '0.02em' }}>
            TiO can make mistakes. Verify important information. Powered by Contextual Synthesis Engine.
          </p>
        </div>
      </footer>
    </div>
  );
}
