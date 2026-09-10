import React, { useState } from 'react';
import { Sun, Moon, Sparkles } from 'lucide-react';
import LoginPanel from './LoginPanel';
import RegistrationPanel from './RegistrationPanel';
import SlidingWindow from './SlidingWindow';
import './Auth.css';

export interface AuthLayoutProps {
  onLoginSuccess?: () => void;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
}

export default function AuthLayout({
  onLoginSuccess,
  theme = 'light',
  onToggleTheme,
}: AuthLayoutProps) {
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');

  const handleToggleMode = () => {
    setAuthMode((prev) => (prev === 'login' ? 'register' : 'login'));
  };

  return (
    <div className="auth-viewport" aria-label="KRIYA Authentication Screen">
      {/* Top Utility Header */}
      <header className="auth-utility-bar">
        <div className="auth-utility-brand">
          <span className="auth-brand-pill">KRIYA SECURITY GATEWAY</span>
        </div>

        <div className="auth-utility-actions">
          {onToggleTheme && (
            <button
              type="button"
              className="auth-utility-btn"
              onClick={onToggleTheme}
              aria-label={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
              <span className="utility-btn-text">{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
            </button>
          )}

          {onLoginSuccess && (
            <button
              type="button"
              className="auth-utility-btn demo-access-btn"
              onClick={onLoginSuccess}
              title="Preview main workbench directly"
            >
              <Sparkles size={14} />
              <span>Enter Workspace (Demo)</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Landscape Master Card */}
      <main className="auth-landscape-card" aria-live="polite">
        {/* Underneath Dual Panels Layout */}
        <div className={`auth-panels-track ${authMode === 'register' ? 'show-register' : 'show-login'}`}>
          {/* LEFT HALF -> LOGIN */}
          <div className="auth-panel-slot slot-login">
            <LoginPanel
              onSwitchToRegister={() => setAuthMode('register')}
              onLoginSuccess={onLoginSuccess}
            />
          </div>

          {/* RIGHT HALF -> REGISTRATION */}
          <div className="auth-panel-slot slot-register">
            <RegistrationPanel
              onSwitchToLogin={() => setAuthMode('login')}
            />
          </div>
        </div>

        {/* Large Horizontal Sliding Window / Overlay */}
        <SlidingWindow
          authMode={authMode}
          onToggleMode={handleToggleMode}
        />
      </main>
    </div>
  );
}
