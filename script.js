let ws = null;
let username = "";
let userColor = "#4a90e2";

function getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws`;
}

function joinChat() {
    const usernameInput = document.getElementById("username");
    const colorPicker = document.getElementById("colorPicker");
    
    username = usernameInput.value.trim();
    userColor = colorPicker.value;
    
    if (!username) {
        alert("Please enter your name");
        return;
    }
    
    // Connect to WebSocket
    ws = new WebSocket(getWebSocketUrl());
    
    ws.onopen = () => {
        // Send user info
        ws.send(JSON.stringify({
            username: username,
            color: userColor
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === "connected") {
            // Show chat screen
            document.getElementById("setupScreen").classList.add("hidden");
            document.getElementById("chatScreen").classList.remove("hidden");
            document.getElementById("messageInput").focus();
            // Update user list with initial users
            if (data.users) {
                updateUserList(data.users);
            }
        } else if (data.type === "user_list") {
            updateUserList(data.users);
        } else if (data.type === "message" || data.type === "join" || data.type === "leave") {
            displayMessage(data);
        }
    };
    
    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        alert("Connection error. Please try again.");
    };
    
    ws.onclose = () => {
        // Return to setup screen
        document.getElementById("chatScreen").classList.add("hidden");
        document.getElementById("setupScreen").classList.remove("hidden");
        document.getElementById("messages").innerHTML = "";
        document.getElementById("usersList").innerHTML = "";
        document.getElementById("userCount").textContent = "0";
    };
}

function leaveChat() {
    if (ws) {
        ws.close();
    }
}

function sendMessage() {
    const messageInput = document.getElementById("messageInput");
    const message = messageInput.value.trim();
    
    if (!message || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }
    
    ws.send(JSON.stringify({
        type: "message",
        message: message
    }));
    
    messageInput.value = "";
}

function displayMessage(data) {
    const messagesDiv = document.getElementById("messages");
    const messageDiv = document.createElement("div");
    
    if (data.type === "join" || data.type === "leave") {
        messageDiv.className = `message message-${data.type}`;
        messageDiv.textContent = data.message;
    } else {
        messageDiv.className = "message";
        const usernameSpan = document.createElement("span");
        usernameSpan.className = "username";
        usernameSpan.style.color = data.color;
        usernameSpan.textContent = data.username + ":";
        
        const contentSpan = document.createElement("span");
        contentSpan.className = "message-content";
        contentSpan.textContent = data.message;
        
        messageDiv.appendChild(usernameSpan);
        messageDiv.appendChild(contentSpan);
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateUserList(users) {
    const usersList = document.getElementById("usersList");
    const userCount = document.getElementById("userCount");
    
    // Update count
    userCount.textContent = users.length.toString();
    
    // Clear and rebuild user list
    usersList.innerHTML = "";
    
    users.forEach(user => {
        const userItem = document.createElement("div");
        userItem.className = "user-item";
        
        const indicator = document.createElement("div");
        indicator.className = "user-indicator";
        
        const nameSpan = document.createElement("span");
        nameSpan.className = "user-name";
        nameSpan.style.color = user.color;
        nameSpan.textContent = user.username;
        
        userItem.appendChild(indicator);
        userItem.appendChild(nameSpan);
        usersList.appendChild(userItem);
    });
}

// Allow sending message with Enter key
document.addEventListener("DOMContentLoaded", () => {
    const messageInput = document.getElementById("messageInput");
    const usernameInput = document.getElementById("username");
    
    messageInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
    
    usernameInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            joinChat();
        }
    });
});

