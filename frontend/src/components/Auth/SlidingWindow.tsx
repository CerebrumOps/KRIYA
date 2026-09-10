import React from 'react';
import { Flame, ArrowRight, ArrowLeft } from 'lucide-react';

export interface SlidingWindowProps {
  authMode: 'login' | 'register';
  onToggleMode: () => void;
}

export default function SlidingWindow({
  authMode,
  onToggleMode,
}: SlidingWindowProps) {
  const isLogin = authMode === 'login';

  return (
    <div className={`sliding-window ${isLogin ? 'pos-login' : 'pos-register'}`} aria-label="Brand overlay card">
      <div className="sliding-window-glass">
        {/* Prominent Application Logo */}
        <div className="sliding-logo-block">
          <div className="sliding-emblem-wrap">
            <div className="sliding-emblem-core">
              <Flame size={32} className="sliding-flame-icon" />
            </div>
          </div>
          <div className="sliding-brand-title">KRIYA</div>
          <div className="sliding-brand-subtitle">Knowledge-based Reasoning & Intelligent Action</div>
        </div>

        {/* Dynamic Contextual Action Area */}
        <div className="sliding-content-body">
          <div
            className={`sliding-state-view view-login ${isLogin ? 'active' : 'inactive'}`}
            aria-hidden={!isLogin}
          >
            <span className="sliding-pill-badge">Employee Onboarding</span>
            <h2 className="sliding-heading">New here?</h2>
            <p className="sliding-description">
              Register as an employee with corporate credentials to access operational intelligence.
            </p>
            <button
              type="button"
              className="sliding-action-btn"
              onClick={onToggleMode}
              id="slide-to-register-btn"
              aria-label="Switch to employee registration"
              tabIndex={isLogin ? 0 : -1}
            >
              <span>Register as an employee</span>
              <ArrowRight size={16} className="sliding-btn-icon" />
            </button>
          </div>

          <div
            className={`sliding-state-view view-register ${!isLogin ? 'active' : 'inactive'}`}
            aria-hidden={isLogin}
          >
            <span className="sliding-pill-badge">Secure Access</span>
            <h2 className="sliding-heading">Already registered?</h2>
            <p className="sliding-description">
              Sign in to continue your session and run plant operations.
            </p>
            <button
              type="button"
              className="sliding-action-btn"
              onClick={onToggleMode}
              id="slide-to-login-btn"
              aria-label="Switch to employee login"
              tabIndex={!isLogin ? 0 : -1}
            >
              <ArrowLeft size={16} className="sliding-btn-icon" />
              <span>Sign in to continue</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
