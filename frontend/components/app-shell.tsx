'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { MessageSquare, Settings, AlertTriangle, Sparkles, Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

const navItems = [
  { href: '/', label: 'Chat', icon: MessageSquare, description: 'Customer Support' },
  { href: '/config', label: 'Config', icon: Settings, description: 'Knowledge Base' },
  { href: '/mistakes', label: 'Mistakes', icon: AlertTriangle, description: 'Error Reports' },
];

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <div className="flex min-h-screen bg-surface">
      {/* Mobile Header */}
      <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center justify-between bg-surface-container-low px-4 lg:hidden">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-dim">
            <Sparkles className="size-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-base font-bold tracking-tight text-foreground">
              Service AI
            </h1>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
        >
          {isMobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
        </Button>
      </header>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm lg:hidden"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}

      {/* Sidebar - Desktop fixed, Mobile drawer */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-surface-container-low transition-transform duration-300 lg:translate-x-0',
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Logo */}
        <div className="flex h-20 items-center gap-3 px-6">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary-dim">
            <Sparkles className="size-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-display text-lg font-bold tracking-tight text-foreground">
              Service AI
            </h1>
            <p className="text-xs text-muted-foreground">Console</p>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6">
          <ul className="space-y-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={closeMobileMenu}
                    className={cn(
                      'group flex items-center gap-3 rounded-xl px-4 py-3 transition-all duration-200',
                      isActive
                        ? 'bg-surface-container-lowest text-foreground'
                        : 'text-muted-foreground hover:bg-surface-container hover:text-foreground'
                    )}
                  >
                    <div
                      className={cn(
                        'flex size-9 items-center justify-center rounded-lg transition-all',
                        isActive
                          ? 'bg-gradient-to-br from-primary to-primary-dim text-primary-foreground'
                          : 'bg-surface-container group-hover:bg-surface-container-high'
                      )}
                    >
                      <Icon className="size-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{item.label}</p>
                      <p className="text-xs text-muted-foreground">{item.description}</p>
                    </div>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Footer */}
        <div className="px-6 py-4">
          <div className="rounded-xl bg-surface-container p-4">
            <p className="text-xs font-medium text-muted-foreground">Meta-Agent Status</p>
            <div className="mt-2 flex items-center gap-2">
              <div className="size-2 animate-pulse rounded-full bg-success" />
              <span className="text-sm text-foreground">Online</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 pt-16 lg:ml-64 lg:pt-0">
        {children}
      </main>
    </div>
  );
}
