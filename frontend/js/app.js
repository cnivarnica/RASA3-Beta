const userInput = document.getElementById('user-input');
const chatBox = document.getElementById('chat-box');

userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    addMessageToChatBox(message, 'user');
    userInput.value = '';
    showTypingIndicator();

    try {
        const response = await fetchBotResponse(message);
        addMessageToChatBox(response, 'bot');
    } catch (error) {
        console.error('Error:', error);
        addMessageToChatBox('Sorry, I encountered an error. Please try again later.', 'bot');
    } finally {
        hideTypingIndicator();
    }
}

async function fetchBotResponse(message) {
    const response = await fetch('http://localhost:5005/webhooks/rest/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });

    if (!response.ok) throw new Error('Network response was not ok');

    const messages = await response.json();
    return messages.map(msg => msg.text).join(' ');
}

function showTypingIndicator() {
    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'bot', 'typing-indicator');
    typingMessage.id = 'typing-indicator';
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    chatBox.appendChild(typingMessage);
    scrollToBottom();
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) typingIndicator.remove();
}

function addMessageToChatBox(message, sender) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', sender);
    messageElement.innerHTML = message.replace(/\n/g, '<br>');
    chatBox.appendChild(messageElement);
    scrollToBottom();
}

function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Initialize chat with a welcome message
function initChat() {
    addMessageToChatBox('Welcome to Rasa Chess-Bot! How can I assist you today?', 'bot');
}

initChat();