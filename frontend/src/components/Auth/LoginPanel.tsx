import React, { useState } from 'react';
import { User, Lock, Eye, EyeOff, KeyRound, ArrowRight, ShieldCheck } from 'lucide-react';
import AuthOtpInput from './AuthOtpInput';

export interface LoginPanelProps {
  onSwitchToRegister: () => void;
  onLoginSuccess?: () => void;
}

export default function LoginPanel({
  onSwitchToRegister,
  onLoginSuccess,
}: LoginPanelProps) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    // UI demonstration transition
    setTimeout(() => {
      setIsSubmitting(false);
      if (onLoginSuccess) {
        onLoginSuccess();
      }
    }, 600);
  };

  return (
    <div className="auth-panel login-panel" aria-label="Existing employee login interface">
      <div className="auth-panel-inner">
        {/* Header */}
        <div className="auth-panel-header">
          <div className="auth-badge-row">
            <span className="auth-context-pill">
              <ShieldCheck size={13} />
              <span>Employee Portal</span>
            </span>
          </div>
          <h1 className="auth-heading">Welcome back</h1>
          <p className="auth-subheading">
            Sign in with your corporate employee credentials and OTP verification to access operational models.
          </p>
        </div>

        {/* Login Form */}
        <form className="auth-form" onSubmit={handleSubmit}>
          {/* Employee ID or Email Input */}
          <div className="auth-field-group">
            <label htmlFor="login-identifier" className="auth-field-label">
              Employee ID or Company Email
            </label>
            <div className="auth-input-wrapper">
              <User size={16} className="auth-field-icon" />
              <input
                id="login-identifier"
                type="text"
                className="auth-input"
                placeholder="Enter Employee ID or company email"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Password Input with Show/Hide Toggle */}
          <div className="auth-field-group">
            <div className="auth-label-row">
              <label htmlFor="login-password" className="auth-field-label">
                Password
              </label>
            </div>
            <div className="auth-input-wrapper">
              <Lock size={16} className="auth-field-icon" />
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="auth-input has-action"
                placeholder="Enter enterprise password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="auth-input-action-btn"
                onClick={() => setShowPassword((prev) => !prev)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* OTP Section */}
          <div className="auth-otp-section">
            <div className="auth-otp-header">
              <div className="auth-otp-title-group">
                <KeyRound size={15} className="auth-otp-icon" />
                <span className="auth-otp-title">Security Code (2FA)</span>
              </div>
              <span className="auth-otp-sent-hint">2FA Security Code</span>
            </div>
            <p className="auth-supporting-text">
              Enter the 6-digit OTP sent to your registered company email
            </p>
            <AuthOtpInput
              value={otp}
              onChange={setOtp}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isSubmitting}
            id="login-submit-btn"
          >
            {isSubmitting ? (
              <span>Authenticating Session...</span>
            ) : (
              <>
                <span>Sign In to Workspace</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Footer Link for New Employees */}
        <div className="auth-panel-footer">
          <span className="auth-footer-text">New employee?</span>
          <button
            type="button"
            className="auth-link-btn"
            onClick={onSwitchToRegister}
            id="login-to-register-link"
          >
            Register here
          </button>
        </div>
      </div>
    </div>
  );
}
