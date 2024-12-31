// static/js/dashboard/chat.js

export function initializeChat() {
  const chatInput = document.getElementById("chatInput");
  const sendButton = document.getElementById("sendButton");
  const chatArea = document.querySelector(".rounded-2xl .flex-1.overflow-y-auto.space-y-4");
  const API_URL = "/api/chat";

  // Update the chat area to prevent horizontal scrolling
  chatArea.style.paddingBottom = "1rem";
  chatArea.style.overflowX = "hidden";

  let isInitialMessageDisplayed = false;
  
  // Function to create avatar
  function createAvatar() {
    const avatar = document.createElement("div");
    avatar.className = "w-10 h-10 bg-[#FC5100] rounded-full flex items-center justify-center flex-shrink-0";
    avatar.innerHTML = `
      <svg id="Laag_2" data-name="Laag 2" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 13.13 13.3" class="w-5 h-5">
        <g id="Laag_1-2" data-name="Laag 1">
          <path d="M1.77.32c.17-.3.55-.41.85-.25.1.06.19.14.25.25l.2.36c.21.38.52.69.89.89l.36.2c.3.17.41.55.25.85-.06.11-.14.19-.25.25l-.36.2c-.38.21-.69.52-.89.89l-.2.36c-.17.3-.55.41-.85.25-.1-.06-.19-.14-.25-.25l-.2-.36c-.21-.38-.52-.69-.89-.89l-.36-.2c-.3-.17-.41-.55-.25-.85.06-.11.14-.19.25-.25l.36-.2c.38-.21.69-.52.89-.89,0,0,.2-.36.2-.36Z" style="fill: #fff;"/>
          <path d="M9.02,3.96c-.18-1.17-1.85-1.19-2.06-.03l-.03.16c-.29,1.56-1.52,2.77-3.09,3.03-1.15.19-1.17,1.83-.03,2.05l.11.02c1.53.3,2.73,1.5,3.03,3.03l.03.17c.23,1.21,1.96,1.21,2.2,0l.02-.13c.3-1.55,1.52-2.76,3.08-3.05,1.18-.22,1.12-1.93-.07-2.11-1.63-.25-2.92-1.52-3.18-3.15h0ZM8.08,10.85c.51-1.15,1.41-2.09,2.54-2.65-1.15-.51-2.08-1.41-2.63-2.55-.52,1.1-1.39,1.98-2.49,2.51,1.15.56,2.07,1.51,2.57,2.69Z" style="fill: #fff; fill-rule: evenodd;"/>
        </g>
      </svg>
    `;
    return avatar;
  }

  function formatMessage(text) {
    // Add proper spacing between words if missing
    text = text.replace(/(?<=[a-zA-Z])(?=[A-Z])/g, ' ');
    // Replace multiple spaces with a single space
    text = text.replace(/\s+/g, ' ');
    return text;
  }

  function showTypingAnimation() {
    const wrapper = document.createElement("div");
    wrapper.className = "flex items-start";
    wrapper.id = "typing-indicator-wrapper";

    const avatar = createAvatar();
    wrapper.appendChild(avatar);

    const bubbleWrapper = document.createElement("div");
    bubbleWrapper.className = "ml-4 max-w-[90%] bg-white border border-[#E7E7E7] rounded-xl p-2 text-[13px] font-medium fm-inter";
    
    const dots = document.createElement("div");
    dots.className = "thinking-dots";
    dots.innerHTML = `
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    `;

    bubbleWrapper.appendChild(dots);
    wrapper.appendChild(bubbleWrapper);
    chatArea.appendChild(wrapper);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function hideTypingAnimation() {
    const wrapper = document.getElementById("typing-indicator-wrapper");
    if (wrapper) wrapper.remove();
  }

  function appendAIMessage(text) {
    const messageWrapper = document.createElement("div");
    messageWrapper.className = "flex items-start";

    const avatar = createAvatar();
    messageWrapper.appendChild(avatar);

    const messageBubble = document.createElement("div");
    messageBubble.className = "ml-4 max-w-[90%] bg-white border border-[#E7E7E7] rounded-xl py-3 px-4 text-[13px] font-normal fm-inter text-[#374151] whitespace-pre-wrap break-words";
    
    // Replace line breaks with <br> tags for HTML rendering
    const formattedText = text.replace(/\n/g, "<br>");
    messageBubble.innerHTML = formattedText; // Ensure innerHTML is used
    
    messageWrapper.appendChild(messageBubble);
    chatArea.appendChild(messageWrapper);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function typewriterEffect(text) {
  const wrapper = document.createElement("div");
  wrapper.className = "flex items-start";

  const avatar = createAvatar();
  wrapper.appendChild(avatar);

  const messageBubble = document.createElement("div");
  messageBubble.className = "ml-4 max-w-[90%] bg-white border border-[#E7E7E7] rounded-xl p-4 text-[13px] font-normal fm-inter text-[#374151] whitespace-pre-wrap break-words";

  wrapper.appendChild(messageBubble);
  chatArea.appendChild(wrapper);

  // Format the text for HTML rendering
  const formattedText = text.replace(/\n/g, "<br>");
  let index = 0;
  const interval = setInterval(() => {
      // Append one character at a time, preserving line breaks
      messageBubble.innerHTML = formattedText.substring(0, index + 1);
      index++;
      chatArea.scrollTop = chatArea.scrollHeight;
      if (index === formattedText.length) {
          clearInterval(interval);
          // Add the personalized message after the welcome message
          if (chatArea.children.length === 1) {
              addPersonalizedMessage();
          }
      }
  }, 3);
}

  function addPersonalizedMessage() {
    const existingMessage = document.querySelector(".personalized-message");
    if (existingMessage) return;

    const personalizedDiv = document.createElement("div");
    personalizedDiv.className = "personalized-message flex items-center space-x-2 mt-3 ml-2";
    personalizedDiv.innerHTML = `
      <img src="/static/images/Person.png" alt="Person Icon" class="w-4 h-4">
      <p class="text-xs text-[#616A75] font-normal fm-inter">
        Answers personalized for <span class="font-semibold">Max</span>
      </p>
    `;
    chatArea.appendChild(personalizedDiv);
  }

  function sendMessage() {
    const message = chatInput.value.trim();
    if (message === "") return;

    const messageWrapper = document.createElement("div");
    messageWrapper.className = "flex items-start justify-end";

    const messageBubble = document.createElement("div");
    messageBubble.className = "bg-[#393342] text-white rounded-xl py-3 px-4 max-w-[80%] text-[13px] font-normal fm-inter whitespace-pre-wrap break-words";
    messageBubble.innerText = message;

    messageWrapper.appendChild(messageBubble);
    chatArea.appendChild(messageWrapper);
    chatInput.value = "";

    showTypingAnimation();
    chatArea.scrollTop = chatArea.scrollHeight;

    const startTime = Date.now();

    fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            message, 
            access_token: sessionStorage.getItem("access_token") // Include the token
        }),
    })
    .then((res) => res.json())
    .then((data) => {
        const timeElapsed = Date.now() - startTime;
        const minDuration = 1000;

        setTimeout(() => {
            hideTypingAnimation();
            typewriterEffect(data.response);
        }, Math.max(0, minDuration - timeElapsed));
    })
    .catch(() => {
        hideTypingAnimation();
        appendAIMessage("Oops! Something went wrong. Please try again.");
    });
}

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  sendButton.addEventListener("click", sendMessage);

  // Reset functionality
  const welcomeMessage = "Hello! My name's Matthew. I'm your virtual assistant. I can help you train better for your next event, or answer questions on your training. How can I help?";
  const resetButton = document.getElementById("resetButton");

  function resetChat() {
  chatArea.innerHTML = ""; // Clear the chat area
  isInitialMessageDisplayed = false; // Reset the tracking flag
  showTypingAnimation(); // Show the typing animation

  setTimeout(() => {
    hideTypingAnimation(); // Hide the typing animation
    typewriterEffect(welcomeMessage); // Start typing the welcome message
    isInitialMessageDisplayed = true; // Set the flag to prevent re-typing
    addPersonalizedMessage(); // Add the personalized message below the chatbot's first message
  }, 1000);

  chatInput.value = ""; // Clear the input field
}

  resetButton.addEventListener("click", resetChat);

}