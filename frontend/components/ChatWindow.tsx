"use client";

import { FormEvent, useState } from "react";

type ChatMessage = { role: "guest" | "agent"; text: string };

// guest_id/conversation_id are fixed for this build -- no auth/session
// wiring yet (explicitly out of scope per the PRD).
const GUEST_ID = "guest-1";
const CONVERSATION_ID = "conv-1";

export function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");

  async function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { role: "guest", text }]);
    setInput("");

    const response = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ guest_id: GUEST_ID, conversation_id: CONVERSATION_ID, message: text }),
    });
    const data = await response.json();
    setMessages((prev) => [...prev, { role: "agent", text: data.reply }]);
  }

  return (
    <div>
      <ul>
        {messages.map((message, index) => (
          <li key={index}>{message.text}</li>
        ))}
      </ul>
      <form onSubmit={sendMessage}>
        <label htmlFor="chat-message">Message</label>
        <input id="chat-message" value={input} onChange={(event) => setInput(event.target.value)} />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
