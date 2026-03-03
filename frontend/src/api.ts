import type { Conversation } from './types'; // Pfad anpassen

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';


let activeAbortController: AbortController | null = null;

export async function getStatus(): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    const data = await response.json();
    return data.status || 'Verbunden';
  } catch {
    return 'Backend nicht erreichbar';
  }
}

export const handleStop = () => {
  if (activeAbortController) {
    activeAbortController.abort();
    activeAbortController = null;
  }
};

export async function handleSend(
  input: string,
  conversationId: string,
  setConversations: React.Dispatch<React.SetStateAction<Conversation[]>>,
  setError: React.Dispatch<React.SetStateAction<string>>
): Promise<{ error?: string; response?: string }> {
  try {
    if (activeAbortController) activeAbortController.abort();
    activeAbortController = new AbortController();
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input }),
      signal: activeAbortController.signal
    });

    const reader = response.body?.getReader();
    if (!reader) throw new Error('Response body is not readable');

    const decoder = new TextDecoder();
    let accumulatedResponse = '';

    
    const assistantMsgId = (Date.now() + 1).toString();
    setConversations(prev => prev.map(c => 
      c.id === conversationId 
        ? {
            ...c,
            messages: [...c.messages, { id: assistantMsgId, text: '', sender: 'assistant', timestamp: new Date() }]
          }
        : c
    ));

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      accumulatedResponse += chunk;
      
      setConversations((prev) => prev.map(c => 
        c.id === conversationId 
          ? {
              ...c,
              messages: c.messages.map(m => 
                m.id === assistantMsgId ? { ...m, text: accumulatedResponse } : m
              )
            }
          : c
      ));
    }
    return { response: accumulatedResponse };
  } catch (error: unknown) {
    if (error instanceof Error && error.name === 'AbortError') {
      console.log('Anfrage abgebrochen');
    } else {
      console.error('Fehler:', error);
      setError('Fehler beim Senden der Nachricht');
    }
    return { error: error instanceof Error ? error.message : 'Unbekannter Fehler' };
  } finally {
    activeAbortController = null;
  }
};