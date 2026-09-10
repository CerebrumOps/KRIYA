import React, { useState } from 'react';
import { Lock, Eye, EyeOff, CheckCircle2, ShieldCheck, ArrowLeft, ArrowRight } from 'lucide-react';

export interface SetPasswordProps {
  onBackToVerification: () => void;
  onSwitchToLogin: () => void;
}

export default function SetPassword({
  onBackToVerification,
  onSwitchToLogin,
}: SetPasswordProps) {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Dynamic visual requirement checks for demonstration
  const reqLength = newPassword.length >= 8;
  const reqUpper = /[A-Z]/.test(newPassword);
  const reqNumber = /\d/.test(newPassword);
  const reqSpecial = /[@$!%*?&#^()_-]/.test(newPassword);
  const passwordsMatch = newPassword.length > 0 && newPassword === confirmPassword;

  const handleSetPassword = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Provide visual demonstration success state
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSuccess(true);
      // After demonstrating success, return to login mode
      setTimeout(() => {
        onSwitchToLogin();
      }, 1600);
    }, 600);
  };

  if (isSuccess) {
    return (
      <div className="registration-stage stage-success" aria-label="Password set success state">
        <div className="auth-success-card">
          <div className="auth-success-icon-wrap">
            <CheckCircle2 size={38} className="auth-success-icon" />
          </div>
          <h2 className="auth-success-title">Password Configured</h2>
          <p className="auth-success-desc">
            Your enterprise employee credentials have been registered and secured under enterprise security policies.
          </p>
          <div className="auth-success-redirect-note">
            <span>Redirecting to Sign In...</span>
          </div>
          <button
            type="button"
            className="auth-submit-btn"
            onClick={onSwitchToLogin}
          >
            <span>Proceed to Login</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="registration-stage stage-password" aria-label="Set password stage">
      {/* Header */}
      <div className="auth-panel-header">
        <div className="auth-badge-row">
          <span className="auth-context-pill">
            <ShieldCheck size={13} />
            <span>Step 2 of 2 • Credential Setup</span>
          </span>
          <button
            type="button"
            className="auth-breadcrumb-back"
            onClick={onBackToVerification}
            title="Return to Employee Verification"
          >
            <ArrowLeft size={12} />
            <span>Change ID</span>
          </button>
        </div>
        <h1 className="auth-heading">Set your password</h1>
        <p className="auth-subheading">
          Create an enterprise password to secure your workstation access.
        </p>
      </div>

      <form className="auth-form" onSubmit={handleSetPassword}>
        {/* New Password Input */}
        <div className="auth-field-group">
          <label htmlFor="reg-new-password" className="auth-field-label">
            New Enterprise Password
          </label>
          <div className="auth-input-wrapper">
            <Lock size={16} className="auth-field-icon" />
            <input
              id="reg-new-password"
              type={showNewPassword ? 'text' : 'password'}
              className="auth-input has-action"
              placeholder="Enter at least 8 characters"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <button
              type="button"
              className="auth-input-action-btn"
              onClick={() => setShowNewPassword((prev) => !prev)}
              title={showNewPassword ? 'Hide password' : 'Show password'}
              aria-label={showNewPassword ? 'Hide password' : 'Show password'}
            >
              {showNewPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>

        {/* Confirm Password Input */}
        <div className="auth-field-group">
          <label htmlFor="reg-confirm-password" className="auth-field-label">
            Confirm Enterprise Password
          </label>
          <div className="auth-input-wrapper">
            <Lock size={16} className="auth-field-icon" />
            <input
              id="reg-confirm-password"
              type={showConfirmPassword ? 'text' : 'password'}
              className="auth-input has-action"
              placeholder="Re-enter enterprise password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
            <button
              type="button"
              className="auth-input-action-btn"
              onClick={() => setShowConfirmPassword((prev) => !prev)}
              title={showConfirmPassword ? 'Hide password' : 'Show password'}
              aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
            >
              {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {confirmPassword && !passwordsMatch && (
            <span className="auth-field-hint error">Passwords do not match yet</span>
          )}
        </div>

        {/* Password Requirements Checklist */}
        <div className="auth-requirements-card">
          <span className="auth-requirements-title">Corporate Password Policy:</span>
          <div className="auth-requirements-grid">
            <div className={`req-item ${reqLength ? 'satisfied' : ''}`}>
              <div className="req-indicator" />
              <span>8+ characters</span>
            </div>
            <div className={`req-item ${reqUpper ? 'satisfied' : ''}`}>
              <div className="req-indicator" />
              <span>1 uppercase letter</span>
            </div>
            <div className={`req-item ${reqNumber ? 'satisfied' : ''}`}>
              <div className="req-indicator" />
              <span>1 numeric digit</span>
            </div>
            <div className={`req-item ${reqSpecial ? 'satisfied' : ''}`}>
              <div className="req-indicator" />
              <span>1 special symbol</span>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="auth-submit-btn"
          disabled={isSubmitting}
          id="set-password-submit-btn"
        >
          {isSubmitting ? (
            <span>Securing Account...</span>
          ) : (
            <>
              <span>Set Password & Finish</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </form>

      {/* Footer Link */}
      <div className="auth-panel-footer">
        <span className="auth-footer-text">Already registered?</span>
        <button
          type="button"
          className="auth-link-btn"
          onClick={onSwitchToLogin}
          id="password-to-login-link"
        >
          Login
        </button>
      </div>
    </div>
  );
}
