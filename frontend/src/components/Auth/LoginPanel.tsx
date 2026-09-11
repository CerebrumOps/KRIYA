import React, { useState } from 'react';
import { User, Lock, Eye, EyeOff, KeyRound, ArrowRight, ShieldCheck, AlertCircle, ArrowLeft } from 'lucide-react';
import AuthOtpInput from './AuthOtpInput';
import { loginCredentials, verifyLoginOtp, storeAuthSession } from '../../api/auth_api';

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
  const [step, setStep] = useState<'credentials' | '2fa'>('credentials');
  const [verificationId, setVerificationId] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');
  const [simulatedOtp, setSimulatedOtp] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const isEmail = identifier.includes('@');
      const resp = await loginCredentials({
        employeeId: isEmail ? undefined : identifier.trim(),
        email: isEmail ? identifier.trim() : undefined,
        password,
      });

      if (resp.credentialsValid && resp.verificationId) {
        setVerificationId(resp.verificationId);
        setMaskedEmail(resp.maskedEmail);
        if (resp.devOtp) {
          setSimulatedOtp(resp.devOtp);
        }
        setStep('2fa');
      } else {
        setErrorMessage('Authentication failed. Please verify your credentials.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid Employee ID or password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOtpSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!otp || otp.length < 6) {
      setErrorMessage('Please enter the full 6-digit security code.');
      return;
    }

    setIsSubmitting(true);
    try {
      const resp = await verifyLoginOtp({
        verificationId,
        otp: otp.trim(),
      });

      if (resp.authenticated && resp.accessToken) {
        storeAuthSession(resp);
        if (onLoginSuccess) {
          onLoginSuccess();
        }
      } else {
        setErrorMessage('Failed to authenticate 2FA security code.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid or expired 2FA security code.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-panel login-panel" aria-label="Existing employee login interface">
      <div className="auth-panel-inner">
        {/* Header */}
        <div className="auth-panel-header">
          <div className="auth-badge-row">
            <span className="auth-context-pill">
              <ShieldCheck size={13} />
              <span>{step === 'credentials' ? 'Employee Portal' : 'Two-Factor Authentication'}</span>
            </span>
            {step === '2fa' && (
              <button
                type="button"
                className="auth-breadcrumb-back"
                onClick={() => {
                  setStep('credentials');
                  setOtp('');
                  setErrorMessage(null);
                }}
                style={{ background: 'none', border: 'none', color: '#0284c7', fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <ArrowLeft size={12} />
                <span>Back</span>
              </button>
            )}
          </div>
          <h1 className="auth-heading">{step === 'credentials' ? 'Welcome back' : 'Verify Security Code'}</h1>
          <p className="auth-subheading">
            {step === 'credentials'
              ? 'Sign in with your corporate employee credentials to access the sovereign AI workbench.'
              : `A 6-digit security code was dispatched to your registered email (${maskedEmail}).`}
          </p>
        </div>

        {errorMessage && (
          <div style={{ padding: '8px 12px', marginBottom: 12, backgroundColor: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 6, color: '#ef4444', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertCircle size={15} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Form */}
        {step === 'credentials' ? (
          <form className="auth-form" onSubmit={handleCredentialsSubmit}>
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
                  placeholder="e.g. EMP-1001 or engineer@mrpl.co.in"
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

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-submit-btn"
              disabled={isSubmitting}
              id="login-submit-btn"
            >
              {isSubmitting ? (
                <span>Validating Credentials...</span>
              ) : (
                <>
                  <span>Continue to 2FA</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleOtpSubmit}>
            {/* OTP Section */}
            <div className="auth-otp-section" style={{ marginTop: 0 }}>
              <div className="auth-otp-header">
                <div className="auth-otp-title-group">
                  <KeyRound size={15} className="auth-otp-icon" />
                  <span className="auth-otp-title">Enter 2FA Code</span>
                </div>
                <span className="auth-otp-sent-hint">Sent to {maskedEmail}</span>
              </div>
              <p className="auth-supporting-text">
                Enter the 6-digit OTP to complete authentication
              </p>
              <AuthOtpInput
                value={otp}
                onChange={setOtp}
              />

              {simulatedOtp && (
                <div style={{
                  marginTop: 14,
                  padding: '10px 14px',
                  background: 'rgba(16, 214, 135, 0.12)',
                  border: '1px solid rgba(16, 214, 135, 0.35)',
                  borderRadius: 8,
                  fontSize: 12,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,
                }}>
                  <div>
                    <span style={{ fontWeight: 600, color: 'var(--c-mint-active)' }}>Air-Gap 2FA Code: </span>
                    <code style={{ fontFamily: 'monospace', fontWeight: 700, fontSize: 13, background: 'rgba(0,0,0,0.08)', padding: '2px 6px', borderRadius: 4, letterSpacing: '0.05em' }}>{simulatedOtp}</code>
                    <div style={{ fontSize: 10, color: 'var(--c-text-muted)', marginTop: 2 }}>Logged to server console (air-gapped gateway)</div>
                  </div>
                  <button
                    type="button"
                    style={{
                      padding: '5px 10px',
                      fontSize: 11,
                      fontWeight: 700,
                      background: 'var(--c-mint)',
                      color: '#0F172A',
                      border: 'none',
                      borderRadius: 4,
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                    onClick={() => setOtp(simulatedOtp)}
                  >
                    Auto-Fill
                  </button>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="auth-submit-btn"
              disabled={isSubmitting}
              id="login-otp-submit-btn"
            >
              {isSubmitting ? (
                <span>Authorizing Session...</span>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>
        )}

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
