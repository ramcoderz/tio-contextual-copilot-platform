import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

export const useChatStore = create((set, get) => ({
  sessionId: localStorage.getItem('tio_session_id') || uuidv4(),
  chatbotId: null,
  history: [],
  isLoading: false,
  isStreaming: false,
  error: null,

  setChatbotId: (id) => set({ chatbotId: id }),

  setSessionFromUser: (uid) => {
    // Persistent user-based session
    const sid = `usr_${uid}`;
    localStorage.setItem('tio_session_id', sid);
    set({ sessionId: sid });
  },

  clearSession: () => {
    const sid = uuidv4();
    localStorage.setItem('tio_session_id', sid);
    set({ sessionId: sid, history: [], chatbotId: null });
  },

  addMessage: (msg) => set((state) => ({ 
    history: [...state.history, { ...msg, id: Date.now() }] 
  })),

  updateLastMessage: (updater) => set((state) => {
    const newHistory = [...state.history];
    if (newHistory.length > 0) {
      const last = newHistory[newHistory.length - 1];
      newHistory[newHistory.length - 1] = { ...last, ...updater(last) };
    }
    return { history: newHistory };
  }),

  setLoading: (val) => set({ isLoading: val }),
  setStreaming: (val) => set({ isStreaming: val }),
  setError: (val) => set({ error: val }),
}));
