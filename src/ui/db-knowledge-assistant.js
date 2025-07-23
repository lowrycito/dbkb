/**
 * Database Knowledge Assistant Web Component
 *
 * A custom web component that provides a chat interface for querying
 * database schema and SQL information.
 */

class DBKnowledgeAssistant extends HTMLElement {
  constructor() {
    super();
    this.apiEndpoint = null;
    this.chatHistory = [];
    this.messageQueue = [];
    this.isProcessing = false;
    this.userContext = null;
    this.sessionId = null;
    this.queryMode = 'smart';
    this.attachShadow({ mode: 'open' });
    this.render();
    this.initEventListeners();
  }

  connectedCallback() {
    // Get API endpoint from attribute or environment
    const apiEndpoint = this.getAttribute('api-endpoint') || 
                       this.getAttribute('data-api-endpoint') ||
                       window.DBKB_API_ENDPOINT ||
                       '';
    
    if (apiEndpoint) {
      this.setApiEndpoint(apiEndpoint);
      // Initialize with user context if available
      if (window.userContext) {
        this.setUserContext(window.userContext);
      }
    } else {
      this.addMessage('assistant', 'Welcome to the Database Knowledge Assistant! Please configure the API endpoint to get started.');
    }
  }

  render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          height: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          --primary-color: #0366d6;
          --secondary-color: #f6f8fa;
          --border-color: #e1e4e8;
          --assistant-bg: #f1f8ff;
          --user-bg: #ffffff;
        }

        .container {
          display: flex;
          flex-direction: column;
          height: 100%;
          max-width: 1200px;
          margin: 0 auto;
        }

        .chat-container {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .message {
          max-width: 85%;
          padding: 12px 16px;
          border-radius: 8px;
          line-height: 1.5;
          position: relative;
        }

        .message.assistant {
          align-self: flex-start;
          background-color: var(--assistant-bg);
          border: 1px solid #d1e5f9;
        }

        .message.user {
          align-self: flex-end;
          background-color: var(--user-bg);
          border: 1px solid var(--border-color);
        }

        .sender {
          font-weight: bold;
          margin-bottom: 4px;
          font-size: 14px;
        }

        .message.assistant .sender {
          color: var(--primary-color);
        }

        .message.user .sender {
          color: #24292e;
        }

        .message-content {
          white-space: pre-wrap;
        }

        .message-content code {
          font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
          background-color: rgba(0, 0, 0, 0.05);
          padding: 2px 4px;
          border-radius: 3px;
        }

        .message-content pre {
          background-color: rgba(0, 0, 0, 0.05);
          padding: 12px;
          border-radius: 6px;
          overflow-x: auto;
          margin: 10px 0;
        }

        .input-container {
          display: flex;
          padding: 16px;
          border-top: 1px solid var(--border-color);
          background-color: white;
        }

        .message-input {
          flex: 1;
          border: 1px solid var(--border-color);
          border-radius: 8px;
          padding: 12px 16px;
          font-size: 14px;
          line-height: 20px;
          resize: none;
          outline: none;
          max-height: 200px;
          overflow-y: auto;
        }

        .message-input:focus {
          border-color: var(--primary-color);
          box-shadow: 0 0 0 3px rgba(3, 102, 214, 0.1);
        }

        .send-button {
          margin-left: 12px;
          padding: 10px 14px;
          background-color: var(--primary-color);
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background-color 0.2s;
          align-self: flex-end;
        }

        .send-button:hover {
          background-color: #0855a4;
        }

        .send-button:disabled {
          background-color: #95c0ee;
          cursor: not-allowed;
        }

        .thinking {
          display: flex;
          gap: 4px;
          padding: 8px 12px;
          background-color: var(--assistant-bg);
          border-radius: 8px;
          align-self: flex-start;
          font-style: italic;
          color: #444;
        }

        .dot {
          width: 8px;
          height: 8px;
          background-color: #888;
          border-radius: 50%;
          animation: pulse 1.5s infinite;
        }

        .dot:nth-child(2) {
          animation-delay: 0.3s;
        }

        .dot:nth-child(3) {
          animation-delay: 0.6s;
        }

        @keyframes pulse {
          0%, 100% { opacity: 0.4; transform: scale(0.8); }
          50% { opacity: 1; transform: scale(1); }
        }
      </style>

      <div class="container">
        <div class="chat-container" id="chatContainer"></div>
        <div class="input-container">
          <textarea
            class="message-input"
            placeholder="Type your query about the database schema or SQL..."
            rows="1"
          ></textarea>
          <button class="send-button" disabled>Send</button>
        </div>
      </div>
    `;
  }

  initEventListeners() {
    const inputEl = this.shadowRoot.querySelector('.message-input');
    const sendButton = this.shadowRoot.querySelector('.send-button');
    const chatContainer = this.shadowRoot.querySelector('#chatContainer');

    // Handle input changes (enable/disable send button)
    inputEl.addEventListener('input', () => {
      const hasText = inputEl.value.trim().length > 0;
      sendButton.disabled = !hasText || !this.apiEndpoint;

      // Auto-resize the textarea
      inputEl.style.height = 'auto';
      const newHeight = Math.min(inputEl.scrollHeight, 200);
      inputEl.style.height = `${newHeight}px`;
    });

    // Handle pressing Enter (without shift) to send
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!sendButton.disabled) {
          this.sendMessage();
        }
      }
    });

    // Handle send button click
    sendButton.addEventListener('click', () => {
      this.sendMessage();
    });

    // Auto-scroll chat container on content change
    const observer = new MutationObserver(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    });

    observer.observe(chatContainer, { childList: true, subtree: true });
  }

  setApiEndpoint(endpoint) {
    // Store the base endpoint
    this.apiEndpoint = endpoint;
    
    // Make sure the endpoint does not end with a slash
    if (this.apiEndpoint.endsWith('/')) {
      this.apiEndpoint = this.apiEndpoint.slice(0, -1);
    }
    
    const sendButton = this.shadowRoot.querySelector('.send-button');
    const inputEl = this.shadowRoot.querySelector('.message-input');
    sendButton.disabled = !inputEl.value.trim().length;
  }

  setUserContext(userContext) {
    this.userContext = userContext;
    
    // Initialize or restore chat session
    this.initializeChatSession();
    
    // Build available knowledge bases info based on application
    const appName = userContext.Application ? userContext.Application.toUpperCase() : 'system';
    const availableKBs = ['database schema', 'support history', 'documentation'];
    const kbList = availableKBs.join(', ');
    
    // Add personalized welcome message
    const welcomeMsg = `Welcome back, ${userContext.FirstName}! I'm here to help you with ${userContext.CompanyName}'s ${appName} ${kbList}. What would you like to know?`;
    this.addMessage('assistant', welcomeMsg);
  }

  setQueryMode(mode) {
    this.queryMode = mode;
    console.log(`Query mode set to: ${mode}`);
  }

  classifyQuery(queryText) {
    // Simple classification logic - can be enhanced with ML later
    const databaseKeywords = [
      'table', 'schema', 'join', 'query', 'sql', 'column', 'index', 'database',
      'select', 'insert', 'update', 'delete', 'create', 'alter', 'drop',
      'foreign key', 'primary key', 'relationship', 'normalize'
    ];
    
    const supportKeywords = [
      'error', 'issue', 'problem', 'slow', 'help', 'troubleshoot', 'bug',
      'performance', 'timeout', 'crash', 'fail', 'broken', 'not working',
      'support', 'ticket', 'resolve', 'fix', 'solution'
    ];
    
    const documentationKeywords = [
      'how to', 'tutorial', 'guide', 'documentation', 'feature', 'setup',
      'configure', 'install', 'getting started', 'best practice',
      'workflow', 'process', 'procedure', 'manual'
    ];
    
    const queryLower = queryText.toLowerCase();
    
    let databaseScore = 0;
    let supportScore = 0;
    let documentationScore = 0;
    
    databaseKeywords.forEach(keyword => {
      if (queryLower.includes(keyword)) databaseScore += 1;
    });
    
    supportKeywords.forEach(keyword => {
      if (queryLower.includes(keyword)) supportScore += 1;
    });
    
    documentationKeywords.forEach(keyword => {
      if (queryLower.includes(keyword)) documentationScore += 1;
    });
    
    // Return the highest scoring category
    if (databaseScore >= supportScore && databaseScore >= documentationScore) {
      return 'database';
    } else if (supportScore >= documentationScore) {
      return 'support';
    } else {
      return 'documentation';
    }
  }

  // KB IDs are now looked up automatically from the application
  // No need for getKnowledgeBaseId function

  async initializeChatSession() {
    if (!this.userContext || !this.apiEndpoint) return;

    try {
      // Check for existing active session or create new one
      const response = await fetch(`${this.apiEndpoint}/chat/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          loginId: this.userContext.LoginId,
          email: this.userContext.Email,
          firstName: this.userContext.FirstName,
          lastName: this.userContext.LastName,
          company: this.userContext.Company,
          companyName: this.userContext.CompanyName,
          industry: this.userContext.Industry,
          databaseHost: this.userContext.DatabaseHost,
          databaseSchema: this.userContext.DatabaseSchema,
          knowledgeBaseId: this.userContext.KnowledgeBaseId
        }),
      });

      if (response.ok) {
        const sessionData = await response.json();
        this.sessionId = sessionData.sessionId;
        
        // Load chat history if session exists
        if (sessionData.messages && sessionData.messages.length > 0) {
          await this.loadChatHistory(sessionData.messages);
        }
      }
    } catch (error) {
      console.error('Failed to initialize chat session:', error);
      // Continue without persistence if database unavailable
    }
  }

  async loadChatHistory(messages) {
    // Clear existing messages and load from database
    const chatContainer = this.shadowRoot.querySelector('#chatContainer');
    chatContainer.innerHTML = '';
    this.chatHistory = [];
    
    messages.forEach(msg => {
      this.addMessage(msg.MessageType, msg.Content, false); // false = don't persist
    });
  }
  
  // Helper method to get the appropriate endpoint based on query type
  getEndpointForQuery(query) {
    // Default to general query endpoint
    let path = '/query';
    
    // Check if this is a specific table relationship query
    const tableMatch = query.match(/(?:relationship|foreign keys|references for|join with)\s+(?:table\s+)?['"]?(\w+)['"]?/i);
    if (tableMatch && tableMatch[1]) {
      return `${this.apiEndpoint}/relationship`;
    }
    
    // Check if this is an SQL optimization query
    if (query.includes('SELECT') && 
        (query.includes('FROM') || query.includes('WHERE')) && 
        query.includes('optimize')) {
      return `${this.apiEndpoint}/optimize`;
    }
    
    return `${this.apiEndpoint}${path}`;
  }

  clearChat() {
    const chatContainer = this.shadowRoot.querySelector('#chatContainer');
    chatContainer.innerHTML = '';
    this.chatHistory = [];
  }

  showThinking() {
    const chatContainer = this.shadowRoot.querySelector('#chatContainer');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'thinking';
    thinkingDiv.id = 'thinking-indicator';

    const dot1 = document.createElement('div');
    const dot2 = document.createElement('div');
    const dot3 = document.createElement('div');
    dot1.className = 'dot';
    dot2.className = 'dot';
    dot3.className = 'dot';

    thinkingDiv.appendChild(dot1);
    thinkingDiv.appendChild(dot2);
    thinkingDiv.appendChild(dot3);

    chatContainer.appendChild(thinkingDiv);
  }

  removeThinking() {
    const thinkingDiv = this.shadowRoot.querySelector('#thinking-indicator');
    if (thinkingDiv) {
      thinkingDiv.remove();
    }
  }

  sendMessage() {
    const inputEl = this.shadowRoot.querySelector('.message-input');
    const userMessage = inputEl.value.trim();

    if (!userMessage || !this.apiEndpoint) return;

    // Add user message to chat
    this.addMessage('user', userMessage, true, {
      queryType: 'user_input',
      timestamp: new Date().toISOString()
    });

    // Clear input field and reset height
    inputEl.value = '';
    inputEl.style.height = 'auto';

    // Disable send button
    this.shadowRoot.querySelector('.send-button').disabled = true;

    // Add to message queue
    this.messageQueue.push(userMessage);
    this.processQueue();
  }

  async processQueue() {
    if (this.isProcessing || this.messageQueue.length === 0) return;

    this.isProcessing = true;
    this.showThinking();

    const userMessage = this.messageQueue.shift();
    
    // Determine query routing based on mode and classification
    let queryTargets = [];
    
    if (this.queryMode === 'smart') {
      // Smart mode: classify query and route accordingly
      const classification = this.classifyQuery(userMessage);
      queryTargets.push({ type: classification });
      
      // If classification confidence is low, query multiple KBs
      if (classification === 'database') {
        // For database queries, also check support history for related issues
        queryTargets.push({ 
          type: 'support', 
          secondary: true 
        });
      }
    } else {
      // Specific mode: query only the selected KB
      queryTargets.push({ type: this.queryMode });
    }
    
    if (queryTargets.length === 0) {
      // Fallback to database KB
      queryTargets.push({ 
        type: 'database'
      });
    }
    
    // Determine which endpoint to use based on the query content
    const endpoint = this.getEndpointForQuery(userMessage);
    
    try {
      // Prepare request payload based on the endpoint
      let requestBody;
      
      if (endpoint.includes('/relationship')) {
        // Extract table name from the query
        const tableMatch = userMessage.match(/(?:relationship|foreign keys|references for|join with)\s+(?:table\s+)?['"]?(\w+)['"]?/i);
        const tableName = tableMatch ? tableMatch[1] : '';
        
        requestBody = {
          table_name: tableName
        };
      } else if (endpoint.includes('/optimize')) {
        // Extract SQL query from the user message
        // This is a simplistic approach - in production you'd want better parsing
        const sqlMatch = userMessage.match(/\b(SELECT\s+.*)\b/is);
        const sqlQuery = sqlMatch ? sqlMatch[1] : userMessage;
        
        requestBody = {
          sql_query: sqlQuery
        };
      } else {
        // General query endpoint
        requestBody = {
          query_text: userMessage
        };
      }
      
      // Add user context and knowledge base routing to request
      if (this.userContext) {
        requestBody.userContext = this.userContext;
        requestBody.sessionId = this.sessionId;
        requestBody.queryTargets = queryTargets;
        requestBody.queryMode = this.queryMode;
      }
      
      // Make the API request
      const startTime = Date.now();
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      const responseTime = Date.now() - startTime;

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const data = await response.json();
      this.removeThinking();

      // Process response based on endpoint
      let assistantResponse = '';
      
      if (endpoint.includes('/relationship') && data.relationship_analysis) {
        assistantResponse = data.relationship_analysis;
      } else if (endpoint.includes('/optimize') && data.optimization_analysis) {
        assistantResponse = data.optimization_analysis;
      } else if (data.answer) {
        assistantResponse = data.answer;
      } else {
        assistantResponse = 'Sorry, I encountered an error processing your request.';
      }
      
      // Add source indicators to response if multiple KBs were queried
      let responseWithSources = assistantResponse;
      if (queryTargets.length > 1 || this.queryMode === 'smart') {
        const primarySource = queryTargets[0]?.type || 'database';
        const sourceIndicator = this.getSourceIndicator(primarySource);
        responseWithSources = assistantResponse + sourceIndicator;
      }
      
      // Add assistant response to chat with metadata
      this.addMessage('assistant', responseWithSources, true, {
        queryType: endpoint.includes('/relationship') ? 'relationship' : 
                   endpoint.includes('/optimize') ? 'optimization' : 'general',
        endpointUsed: endpoint.split('/').pop(),
        responseTime: responseTime,
        queryTargets: queryTargets,
        queryMode: this.queryMode
      });
    } catch (error) {
      console.error('Error:', error);
      this.removeThinking();
      this.addMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
    }

    this.isProcessing = false;

    // Process next message in queue if any
    if (this.messageQueue.length > 0) {
      setTimeout(() => this.processQueue(), 300);
    }
  }

  addMessage(sender, content, persist = true, metadata = {}) {
    const chatContainer = this.shadowRoot.querySelector('#chatContainer');

    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message ${sender}`;

    // Create sender label
    const senderEl = document.createElement('div');
    senderEl.className = 'sender';
    senderEl.textContent = sender === 'user' ? 'You' : 'Assistant';

    // Create content element with markdown-like formatting
    const contentEl = document.createElement('div');
    contentEl.className = 'message-content';

    // Simple markdown-like formatting
    let formattedContent = content
      // Code blocks (```code```)
      .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
      // Inline code (`code`)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Bold (**text**)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic (*text*)
      .replace(/\*([^\*]+)\*/g, '<em>$1</em>')
      // Line breaks
      .replace(/\n/g, '<br>');

    contentEl.innerHTML = formattedContent;

    // Append elements
    messageEl.appendChild(senderEl);
    messageEl.appendChild(contentEl);
    chatContainer.appendChild(messageEl);

    // Save to chat history
    this.chatHistory.push({
      role: sender,
      content: content,
      timestamp: new Date().toISOString(),
      metadata: metadata
    });

    // Persist to database if enabled and we have session context
    if (persist && this.sessionId && this.userContext) {
      this.persistMessage(sender, content, metadata);
    }
  }

  getSourceIndicator(sourceType) {
    const indicators = {
      'database': '<span class="source-indicator source-database">📊 Database</span>',
      'support': '<span class="source-indicator source-support">🎫 Support</span>',
      'documentation': '<span class="source-indicator source-documentation">📚 Documentation</span>'
    };
    
    return indicators[sourceType] || '';
  }

  async persistMessage(sender, content, metadata = {}) {
    try {
      await fetch(`${this.apiEndpoint}/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sessionId: this.sessionId,
          messageType: sender,
          content: content,
          metadata: metadata,
          userContext: this.userContext
        }),
      });
    } catch (error) {
      console.error('Failed to persist message:', error);
      // Continue silently - chat still works without persistence
    }
  }
}

customElements.define('db-knowledge-assistant', DBKnowledgeAssistant);