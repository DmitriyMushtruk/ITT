/**
 * AI Helper - JavaScript
 * Handles the frontend logic for the AI Helper application
 */

// DOM Elements
const conversationSection = document.querySelector('.conversation-section');
const conversationContainer = document.querySelector('.conversation-container');
const questionInput = document.getElementById('questionInput');
const askButton = document.getElementById('askButton');
const loadingSpinner = document.getElementById('loadingSpinner');
const themeToggle = document.getElementById('themeToggle');

// State
let conversationHistory = [];
let isLoading = false;

// Initialize the application
function init() {
  // Auto-resize textarea as user types
  setupTextareaAutoResize();

  // Set up event listeners
  setupEventListeners();

  // Initialize theme based on system preference
  initializeTheme();

  // Load conversation history on initial load
  fetchConversationHistory();
}

// Setup event listeners
function setupEventListeners() {
  // Send question on button click
  askButton.addEventListener('click', handleAskQuestion);

  // Send question on Enter key (but allow Shift+Enter for new lines)
  questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAskQuestion();
    }
  });

  // Toggle theme
  themeToggle.addEventListener('click', toggleTheme);
}

// Handle asking a question
async function handleAskQuestion() {
  const question = questionInput.value.trim();

  if (!question || isLoading) {
    return;
  }

  try {
    // Show loading state
    setLoading(true);

    // Add user message to UI immediately
    addMessageToUI('user', question);

    // Clear input
    questionInput.value = '';
    questionInput.style.height = 'auto';

    // Send request to backend
    const response = await askQuestion(question);

    // Add AI response to UI
    addMessageToUI('ai', response.answer, false, response.created_at);

    // Update conversation history
    await fetchConversationHistory();

  } catch (error) {
    showError(error.message);
  } finally {
    setLoading(false);
  }
}

// Send question to API
async function askQuestion(question) {
  const response = await fetch('/api/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to get a response');
  }

  return await response.json();
}

// Fetch conversation history from API
async function fetchConversationHistory() {
  try {
    const response = await fetch('/api/history');

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch history');
    }

    const data = await response.json();

    // Update local history
    conversationHistory = data.reverse(); // Reverse to show oldest first

    // Update UI with new history
    renderConversationHistory();

  } catch (error) {
    console.error('Error fetching history:', error);
  }
}

// Render conversation history in the UI
function renderConversationHistory() {
  // Clear current content
  conversationContainer.innerHTML = '';

  if (!conversationHistory.length) {
    // Show empty state if no history
    showEmptyState();
    return;
  }

  // Add each conversation item to the UI in chronological order
  conversationHistory.forEach(item => {
    addMessageToUI('user', item.question, true, item.created_at);
    addMessageToUI('ai', item.answer, true, item.created_at);
  });

  // Scroll to bottom of conversation
  requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            scrollToBottom();
        });
    });
}

// Add a message to the UI
function addMessageToUI(role, content, isHistoryItem = false, timestamp = null) {
  // Remove empty state if present
  const emptyState = conversationContainer.querySelector('.empty-state');
  if (emptyState) {
    conversationContainer.removeChild(emptyState);
  }

  // Create message container
  const messageElement = document.createElement('div');
  messageElement.className = `message message-${role === 'user' ? 'user' : 'ai'}`;

  // Create message bubble
  const bubbleElement = document.createElement('div');
  bubbleElement.className = 'message-bubble';
  bubbleElement.textContent = content;

  // Create timestamp
  const timestampElement = document.createElement('div');
  timestampElement.className = 'message-timestamp';
  timestampElement.textContent = timestamp ? formatTimestamp(new Date(timestamp)) : formatTimestamp(new Date());

  // Assemble message
  messageElement.appendChild(bubbleElement);
  messageElement.appendChild(timestampElement);

  // Add to conversation container at the end
  conversationContainer.appendChild(messageElement);

  // Only scroll for new messages, not when loading history
  if (!isHistoryItem) {
    scrollToBottom();
  }
}

// Show empty state
function showEmptyState() {
  const emptyStateHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">
        <span class="material-symbols-rounded">chat</span>
      </div>
      <p>Ask a question to start the conversation</p>
    </div>
  `;
  conversationContainer.innerHTML = emptyStateHTML;
}

// Show error message
function showError(message) {
  const errorElement = document.createElement('div');
  errorElement.className = 'error-message';
  errorElement.textContent = `Error: ${message}`;

  conversationContainer.appendChild(errorElement);
  scrollToBottom();

  // Remove error after 5 seconds
  setTimeout(() => {
    if (errorElement.parentNode) {
      errorElement.parentNode.removeChild(errorElement);
    }
  }, 5000);
}

// Set loading state
function setLoading(loading) {
  isLoading = loading;

  if (loading) {
    loadingSpinner.classList.add('visible');
    askButton.disabled = true;
  } else {
    loadingSpinner.classList.remove('visible');
    askButton.disabled = false;
  }
}

// Auto-resize textarea as user types
function setupTextareaAutoResize() {
  questionInput.addEventListener('input', () => {
    questionInput.style.height = 'auto';
    questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + 'px';
  });
}

// Format timestamp
function formatTimestamp(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Scroll to bottom of conversation
function scrollToBottom() {
    const lastMessage = conversationContainer.lastElementChild;
    if (lastMessage) {
        lastMessage.scrollIntoView({ behavior: "instant", block: "end" });
    } else {
        conversationSection.scrollTop = conversationSection.scrollHeight;
    }
}


// Theme handling
function initializeTheme() {
  // Check if user has a saved preference
  const savedTheme = localStorage.getItem('theme');

  if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    themeToggle.querySelector('.material-symbols-rounded').textContent = 'light_mode';
  } else if (savedTheme === 'light') {
    document.body.classList.add('light-theme');
  }
  // Otherwise, use system preference (handled by CSS)
}

// Toggle between light and dark theme
function toggleTheme() {
  const isDarkTheme = document.body.classList.contains('dark-theme');

  if (isDarkTheme) {
    // Switch to light theme
    document.body.classList.remove('dark-theme');
    document.body.classList.add('light-theme');
    localStorage.setItem('theme', 'light');
    themeToggle.querySelector('.material-symbols-rounded').textContent = 'dark_mode';
  } else {
    // Switch to dark theme
    document.body.classList.remove('light-theme');
    document.body.classList.add('dark-theme');
    localStorage.setItem('theme', 'dark');
    themeToggle.querySelector('.material-symbols-rounded').textContent = 'light_mode';
  }
}

// Initialize the application
init();