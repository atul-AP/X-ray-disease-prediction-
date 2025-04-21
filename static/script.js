document.addEventListener("DOMContentLoaded", function () {
    // ==== Initialize Flatpickr Date Picker ====
    flatpickr("#dateInput", {
      enableTime: false,
      dateFormat: "Y-m-d",
    });

    const ctx = document.getElementById('diseaseChart').getContext('2d');
    ctx.canvas.height = 300;

  
    // ==== Chatbot Functionality ====
    const chatInput = document.getElementById("chat_input");
    const chatMessages = document.getElementById("chatMessages");
    const sendButton = document.getElementById("sendButton");
  
    // Function to append messages to the chatbox
    function appendMessage(sender, message) {
      const messageDiv = document.createElement("div");
      messageDiv.className = `${sender}-message`;
      messageDiv.textContent = message;
      chatMessages.appendChild(messageDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  
    // Function to handle sending messages
    function sendMessage() {
      const userMessage = chatInput.value.trim();
      if (!userMessage) return;
  
      // Display user's message
      appendMessage("user", userMessage);
      chatInput.value = "";
  
      // Display AI thinking message
      const aiThinkingMessage = document.createElement("div");
      aiThinkingMessage.className = "ai-message";
      aiThinkingMessage.textContent = "🤖 Thinking...";
      chatMessages.appendChild(aiThinkingMessage);
      chatMessages.scrollTop = chatMessages.scrollHeight;
  
      // Send user's message to Flask backend
      fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage }),
      })
        .then((response) => response.json())
        .then((data) => {
          aiThinkingMessage.remove(); // Remove "Thinking..." message
          if (data.response) {
            appendMessage("ai", data.response);
          } else {
            appendMessage("ai", "❌ Unexpected response from the server.");
          }
        })
        .catch((error) => {
          aiThinkingMessage.remove();
          appendMessage("ai", `❌ Error: ${error.message}`);
        });
    }
  
    // Event listener for send button
    sendButton.addEventListener("click", sendMessage);
  
    // Optional: Allow sending message with Enter key
    chatInput.addEventListener("keypress", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
      }
    });
  });
  document.addEventListener("DOMContentLoaded", function () {
    // === Existing chatbot and chart code ===
  
    // ==== Report Actions Handling ====
    document.querySelectorAll(".report-card").forEach((card) => {
      const reportId = card.getAttribute("data-id");
  
      // Download PDF
      card.querySelector(".btn-download")?.addEventListener("click", () => {
        if (reportId) {
          window.location.href = `/download_report/${reportId}`;
        } else {
          alert("❌ Report ID missing!");
        }
      });
      
  
      // Share Report (WhatsApp/Email prompt)
      card.querySelector(".btn-share")?.addEventListener("click", () => {
        const userName = card.querySelector("h3")?.textContent || "Someone";
        const disease = card.querySelector("p strong")?.nextSibling?.textContent || "";
        const imageUrl = card.querySelector("img")?.src || "";
  
        const shareText = `${userName} has been diagnosed with ${disease.trim()}. You can check the full report here: ${window.location.href}`;
        const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
  
        const choice = confirm("Do you want to share this via WhatsApp?");
        if (choice) {
          window.open(whatsappUrl, "_blank");
        } else {
          // fallback: Email
          const subject = "X-Ray Report Summary";
          const emailUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(shareText)}`;
          window.location.href = emailUrl;
        }
      });
    });
  });
  