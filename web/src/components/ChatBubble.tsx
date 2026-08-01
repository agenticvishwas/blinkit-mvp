export default function ChatBubble({ role, content }: { role: "user" | "assistant"; content: string }) {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-2`}>
      <div
        className={`max-w-[78%] rounded-2xl px-3.5 py-2.5 text-sm leading-snug ${
          isUser ? "bg-coral-500 text-white rounded-br-sm" : "bg-sand-100 text-ink-900 rounded-bl-sm"
        }`}
      >
        {content}
      </div>
    </div>
  );
}
