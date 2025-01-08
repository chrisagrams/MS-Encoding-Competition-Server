import { Header } from './Header';

import { ReactNode } from 'react';

export const Layout = ({ children }: { children: ReactNode }) => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1">{children}</main>
    </div>
  );
};