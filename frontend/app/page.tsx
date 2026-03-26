import { AppShell } from '@/components/app-shell';
import { ChatContainer } from '@/components/chat/chat-container';

export default function ChatPage() {
  return (
    <AppShell>
      <div className="flex h-screen flex-col bg-surface">
        {/* Header */}
        <header className="flex h-16 items-center justify-between border-b border-surface-container-high bg-surface-container-lowest px-8">
          <div>
            <h1 className="text-lg font-semibold text-foreground">
              Customer Support Chat
            </h1>
            <p className="text-sm text-muted-foreground">
              AI-powered assistance for your queries
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-lg bg-success/10 px-3 py-1.5">
            <div className="size-2 rounded-full bg-success" />
            <span className="text-sm font-medium text-success">Online</span>
          </div>
        </header>

        {/* Chat Container */}
        <div className="flex-1 overflow-hidden">
          <ChatContainer />
        </div>
      </div>
    </AppShell>
  );
}
