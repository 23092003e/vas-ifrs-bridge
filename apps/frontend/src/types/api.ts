export interface ChatRequest {
  conversation_id?: string
  content: string
  lang: 'vi' | 'en' | 'auto'
  scope: 'shared' | 'tenant' | 'both'
}

export interface ChatTokenEvent { type: 'token'; delta: string }
export interface ChatCitationEvent { type: 'citation'; key: string; doc_id: string; snippet: string }
