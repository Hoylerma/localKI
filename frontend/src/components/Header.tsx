import { Menu } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
}

function Header({ onToggleSidebar }: HeaderProps) {
  return (
    <header className="bg-[#000000] text-white flex-shrink-0">
      <div className="flex items-center px-4 py-3 gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-1 rounded hover:bg-white/10 transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu size={24} />
        </button>
        <span className="text-[#ffe000] text-lg font-semibold">
          Bw-I Chatbot - Intelligente Hilfe
        </span>
      </div>
    </header>
  );
}

export default Header;
