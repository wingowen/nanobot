/**
 * JavaScript/TypeScript client for NanoBOT HTTP API
 *
 * Usage in browser or Node.js with fetch/axios
 */

class NanoBotClient {
  /**
   * Create client
   * @param {string} baseUrl API base URL
   * @param {string} apiKey API key for authentication
   */
  constructor(baseUrl = 'http://localhost:8000', apiKey = null) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
    this.headers = {
      'Content-Type': 'application/json',
      ...(apiKey && { 'X-API-Key': apiKey })
    };
  }

  /**
   * Send a chat message
   * @param {string} message User message
   * @param {Object} options Options
   * @param {string} options.userId User identifier (default: 'api_user')
   * @param {string} options.sessionId Session identifier
   * @param {string} options.model Model override
   * @param {boolean} options.stream Stream response (default: false)
   * @returns {Promise<string|AsyncGenerator<string>>}
   */
  async chat(message, options = {}) {
    const {
      userId = 'api_user',
      sessionId = null,
      model = null,
      stream = false
    } = options;

    const payload = {
      model,
      messages: [{ role: 'user', content: message }],
      stream,
      user: userId,
      session_id: sessionId
    };

    const response = await fetch(`${this.baseUrl}/v1/chat/completions`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || `HTTP ${response.status}`);
    }

    if (stream) {
      // Return an async generator for SSE
      return this._streamResponse(response);
    } else {
      const data = await response.json();
      return data.choices[0].message.content;
    }
  }

  /**
   * Stream response generator
   * @private
   */
  async *_streamResponse(response) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') return;
          try {
            const chunk = JSON.parse(data);
            if (chunk.choices?.[0]?.delta?.content) {
              yield chunk.choices[0].delta.content;
            }
          } catch (e) {
            // Skip malformed lines
          }
        }
      }
    }
  }

  /**
   * List sessions for a user
   * @param {string} userId
   * @returns {Promise<Array>}
   */
  async listSessions(userId = 'api_user') {
    const response = await fetch(
      `${this.baseUrl}/v1/sessions/${userId}`,
      { headers: this.headers }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  /**
   * Delete a session
   * @param {string} sessionId
   * @param {string} userId
   * @returns {Promise<Object>}
   */
  async deleteSession(sessionId, userId = 'api_user') {
    const response = await fetch(
      `${this.baseUrl}/v1/sessions/${sessionId}?user_id=${encodeURIComponent(userId)}`,
      { method: 'DELETE', headers: this.headers }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  /**
   * List available tools
   * @returns {Promise<Array>}
   */
  async listTools() {
    const response = await fetch(
      `${this.baseUrl}/v1/tools`,
      { headers: this.headers }
    );
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return data.tools;
  }

  /**
   * Health check
   * @returns {Promise<Object>}
   */
  async health() {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { NanoBotClient };
}

// Example usage
if (typeof window !== 'undefined') {
  // Browser usage:
  // const client = new NanoBotClient('https://api.example.com', 'your-api-key');
  // const response = await client.chat('Hello!');
}

if (typeof require === 'function' && require.main === module) {
  // Node.js example
  (async () => {
    const client = new NanoBotClient('http://localhost:8000', 'your-api-key');

    try {
      // Simple query
      const response = await client.chat('What can you do?');
      console.log('Response:', response);

      // Streaming
      console.log('\nStreaming:');
      const stream = await client.chat('Tell me a short story', { stream: true });
      for await (const chunk of stream) {
        process.stdout.write(chunk);
      }
      console.log();

      // List sessions
      const sessions = await client.listSessions();
      console.log('Sessions:', sessions);
    } catch (error) {
      console.error('Error:', error.message);
    }
  })();
}
