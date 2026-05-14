import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { 
  Globe, ArrowRight, Loader2, Upload, FileText, 
  CheckCircle2, XCircle, Bot, Sparkles, ChevronRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const STAGES = ["Crawling", "Extracting", "Synthesizing", "Vectorizing", "Ready"];

export default function CreateChatbotPage() {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [step, setStep] = useState(1);
  const [status, setStatus] = useState("pending");
  const [stage, setStage] = useState(0);
  const [error, setError] = useState("");
  const [files, setFiles] = useState([]);
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const handleCreate = async () => {
    if (!url.trim()) return;
    setStatus("creating");
    setError("");

    try {
      const bot = await api("/chatbots", {
        method: "POST",
        body: JSON.stringify({ website_url: url, name: name || url.split('/')[2] })
      });
      setStep(2);
      pollStatus(bot.id);
    } catch (err) {
      setError(err.message || "Failed to initiate ingestion");
      setStatus("error");
    }
  };

  const pollStatus = (id) => {
    const interval = setInterval(async () => {
      try {
        const bot = await api(`/chatbots/${id}`);
        setStatus(bot.status);
        
        // Mocking stages for UI feel
        if (bot.status === 'ingesting') {
          setStage(prev => Math.min(prev + 1, 3));
        } else if (bot.status === 'ready') {
          setStage(4);
          clearInterval(interval);
          setTimeout(() => navigate(`/chat`), 2000);
        } else if (bot.status === 'error') {
          clearInterval(interval);
        }
      } catch (err) {
        clearInterval(interval);
      }
    }, 3000);
  };

  const handleUpload = async (fileList) => {
    // Basic multi-file upload logic
    const newFiles = Array.from(fileList).map(f => ({ name: f.name, status: 'uploading' }));
    setFiles(prev => [...prev, ...newFiles]);
    // In a real app, we'd send to backend here
  };

  const progressPercent = (stage + 1) * 20;

  return (
    <div className="page-container" style={{ maxWidth: '640px', margin: '0 auto', padding: '60px 24px' }}>
      <div style={{ textAlign: 'center', marginBottom: '40px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: '12px' }}>
          Build Your <span className="text-gradient">Copilot</span>
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '16px' }}>
          Connect a website to synthesize context and create an intelligent agent.
        </p>
      </div>

      {/* Step 1: URL + Name */}
      {step === 1 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-panel" style={{ padding: '28px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Website URL</label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
            <Globe size={18} color="var(--text-muted)" style={{ flexShrink: 0 }} />
            <input
              className="input"
              placeholder="https://example.com"
              value={url}
              onChange={e => setUrl(e.target.value)}
              autoFocus
            />
          </div>

          <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>Name (optional)</label>
          <input
            className="input"
            placeholder="Auto-generated from URL"
            value={name}
            onChange={e => setName(e.target.value)}
            style={{ marginBottom: '24px' }}
          />

          {error && <p style={{ color: 'var(--accent-red)', fontSize: '13px', marginBottom: '16px' }}>{error}</p>}

          <button
            onClick={handleCreate}
            disabled={!url.trim() || status === 'creating'}
            className="btn btn-primary"
            style={{ width: '100%', justifyContent: 'center', opacity: !url.trim() ? 0.4 : 1 }}
          >
            {status === 'creating' ? <><Loader2 size={16} className="animate-spin" /> Creating...</> : <><ArrowRight size={16} /> Create & Start Ingestion</>}
          </button>
        </motion.div>
      )}

      {/* Step 2: Ingestion Progress */}
      {step === 2 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <div className="glass-panel" style={{ padding: '28px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <p style={{ fontSize: '14px', fontWeight: 700 }}>
                {status === 'ready' ? '✅ Chatbot Ready!' : status === 'error' ? '❌ Ingestion Failed' : 'Processing Website...'}
              </p>
              <span className={`badge ${status === 'ready' ? 'badge-green' : status === 'error' ? 'badge-red' : 'badge-amber badge-pulse'}`}>
                {status === 'ready' ? 'Complete' : status === 'error' ? 'Error' : STAGES[stage]}
              </span>
            </div>

            <div className="progress-bar" style={{ height: '8px', background: 'var(--bg-card)', borderRadius: '4px', overflow: 'hidden' }}>
              <motion.div 
                animate={{ width: `${progressPercent}%` }}
                style={{ height: '100%', background: 'var(--accent)', boxShadow: 'var(--accent-glow)' }} 
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
              {STAGES.map((s, i) => (
                <span key={s} style={{
                  fontSize: '11px', fontWeight: 600, 
                  color: i <= stage ? 'var(--accent)' : 'var(--text-dim)'
                }}>
                  {i <= stage ? '●' : '○'} {s}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
