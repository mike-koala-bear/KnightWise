'use client';

import { Home, Map, Swords, Zap } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/app',    label: 'Home',     Icon: Home,   color: 'text-kw-green'  },
  { href: '/galaxy', label: 'Path',     Icon: Map,    color: 'text-kw-purple' },
  { href: '/warp',   label: 'Learn',    Icon: Zap,    color: 'text-kw-yellow' },
  { href: '/drill',  label: 'Drill',    Icon: Swords, color: 'text-kw-blue'   },
] as const;

const HIDE_ON = ['/', '/sign-in', '/sign-up'];

export function BottomNav() {
  const pathname = usePathname();

  if (HIDE_ON.some((p) => pathname === p || pathname.startsWith(p + '/'))) {
    return null;
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-kw-border bg-kw-bg/95 backdrop-blur-sm pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto flex max-w-lg justify-around">
        {NAV_ITEMS.map(({ href, label, Icon, color }) => {
          const active = pathname === href || (href !== '/app' && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-1 px-5 py-3 transition-colors ${
                active ? color : 'text-slate-600 hover:text-slate-400'
              }`}
            >
              <Icon className={`h-6 w-6 ${active ? `${color} ${active ? 'drop-shadow-sm' : ''}` : ''}`} strokeWidth={active ? 2.5 : 1.75} />
              <span className={`text-[10px] font-bold uppercase tracking-wider ${active ? color : 'text-slate-600'}`}>
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
