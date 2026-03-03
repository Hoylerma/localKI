import {
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  MessagePartPrimitive,
} from '@assistant-ui/react';
import { MarkdownTextPrimitive } from '@assistant-ui/react-markdown';
import { SendHorizonal, Square } from 'lucide-react';

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end px-4 pb-4 w-full max-w-[1200px] mx-auto">
      <div className="max-w-[70%] bg-[#ffe000] text-black rounded-lg p-3 text-sm">
        <MessagePrimitive.Parts
          components={{
            Text: () => (
              <MessagePartPrimitive.Text
                component="p"
                className="whitespace-pre-wrap break-words"
              />
            ),
          }}
        />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-start px-4 pb-4 w-full max-w-[1200px] mx-auto">
      <div className="max-w-[70%] bg-[#ededed] text-black rounded-lg p-3 text-sm">
        <MessagePrimitive.Parts
          components={{
            Text: () => <MarkdownTextPrimitive className="prose prose-sm max-w-none" />,
            Empty: () => (
              <MessagePartPrimitive.InProgress>
                <span className="inline-flex gap-1">
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:300ms]" />
                </span>
              </MessagePartPrimitive.InProgress>
            ),
          }}
        />
      </div>
    </MessagePrimitive.Root>
  );
}

export default function Thread() {
  return (
    <ThreadPrimitive.Root className="flex flex-col h-full">
      <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto py-4">
        <ThreadPrimitive.Empty>
          <div className="flex items-center justify-center h-full min-h-[400px] text-gray-400">
            <span className="text-xl">Starte eine neue Konversation</span>
          </div>
        </ThreadPrimitive.Empty>
        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            AssistantMessage,
          }}
        />
      </ThreadPrimitive.Viewport>

      <div className="border-t border-[#dadada] bg-[#f6f6f6] p-4 flex-shrink-0">
        <ComposerPrimitive.Root className="flex gap-2 max-w-[1200px] mx-auto">
          <ComposerPrimitive.Input
            className="flex-1 border border-gray-300 rounded px-3 py-2 bg-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-[#ffe000] focus:border-transparent"
            placeholder="Schreibe eine Nachricht..."
            rows={1}
          />
          <ComposerPrimitive.Send className="bg-[#ffe000] text-black px-4 py-2 rounded font-medium text-sm hover:brightness-95 disabled:opacity-40 flex items-center gap-1 cursor-pointer disabled:cursor-not-allowed whitespace-nowrap">
            <SendHorizonal size={16} />
            SENDEN
          </ComposerPrimitive.Send>
          <ComposerPrimitive.Cancel className="hidden bg-[#ededed] text-black px-4 py-2 rounded font-medium text-sm hover:brightness-95 items-center gap-1 cursor-pointer [&:not([disabled])]:flex">
            <Square size={14} />
            STOPP
          </ComposerPrimitive.Cancel>
        </ComposerPrimitive.Root>
      </div>
    </ThreadPrimitive.Root>
  );
}
