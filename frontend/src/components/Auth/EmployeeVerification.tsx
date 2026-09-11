import React, { useState } from 'react';
import { User, ShieldCheck, Mail, Briefcase, Building2, MapPin, KeyRound, ArrowRight, Lock, AlertCircle, RefreshCw } from 'lucide-react';
import AuthOtpInput from './AuthOtpInput';
import { Employee } from '../../schemas/employee';
import { fetchEmployeeDetails, sendRegistrationOtp, verifyRegistrationOtp } from '../../api/auth_api';

export interface EmployeeVerificationProps {
  onAdvanceToPassword: (employeeId: string, verificationToken: string) => void;
  onSwitchToLogin: () => void;
}

export default function EmployeeVerification({
  onAdvanceToPassword,
  onSwitchToLogin,
}: EmployeeVerificationProps) {
  const [employeeId, setEmployeeId] = useState('');
  const [otp, setOtp] = useState('');
  const [isLookingUp, setIsLookingUp] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [employeeData, setEmployeeData] = useState<Employee | null>(null);
  const [simulatedOtp, setSimulatedOtp] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleLookupAndSendOtp = async (idToLookUp?: string) => {
    const id = (idToLookUp || employeeId).trim();
    if (!id) return;
    setIsLookingUp(true);
    setErrorMessage(null);
    try {
      // 1. Fetch directory record
      const fetchResp = await fetchEmployeeDetails({ employeeId: id });
      setEmployeeData(fetchResp.employee);

      // 2. Dispatch OTP
      const otpResp = await sendRegistrationOtp({ employeeId: id });
      setSuccessMessage(`OTP sent to ${otpResp.maskedEmail}. Check your inbox.`);
      if (otpResp.devOtp) {
        setSimulatedOtp(otpResp.devOtp);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to verify employee record.');
      setEmployeeData(null);
    } finally {
      setIsLookingUp(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // If employeeData not fetched yet, fetch first
    if (!employeeData) {
      await handleLookupAndSendOtp();
      return;
    }

    if (!otp || otp.length < 6) {
      setErrorMessage('Please enter the complete 6-digit verification code.');
      return;
    }

    setIsVerifying(true);
    try {
      const resp = await verifyRegistrationOtp({
        employeeId: employeeId.trim(),
        otp: otp.trim(),
      });
      if (resp.verified && resp.verificationToken) {
        onAdvanceToPassword(employeeId.trim(), resp.verificationToken);
      } else {
        setErrorMessage('Verification failed. Please check the code.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Invalid verification code.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="registration-stage stage-verification" aria-label="Employee verification stage">
      {/* Header */}
      <div className="auth-panel-header">
        <div className="auth-badge-row">
          <span className="auth-context-pill">
            <ShieldCheck size={13} />
            <span>Step 1 of 2 • Identity Verification</span>
          </span>
        </div>
        <h1 className="auth-heading">Employee Registration</h1>
        <p className="auth-subheading">
          Enter your assigned corporate Employee ID to verify your organizational profile and generate onboarding OTP.
        </p>
      </div>

      {errorMessage && (
        <div style={{ padding: '8px 12px', marginBottom: 12, backgroundColor: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 6, color: '#ef4444', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertCircle size={15} />
          <span>{errorMessage}</span>
        </div>
      )}

      {successMessage && (
        <div style={{ padding: '8px 12px', marginBottom: 12, backgroundColor: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: 6, color: '#10b981', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldCheck size={15} />
          <span>{successMessage}</span>
        </div>
      )}

      <form className="auth-form" onSubmit={handleVerify}>
        {/* Editable Employee ID Input */}
        <div className="auth-field-group">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <label htmlFor="reg-emp-id" className="auth-field-label">
              Assigned Employee ID
            </label>
            <button
              type="button"
              onClick={() => handleLookupAndSendOtp()}
              disabled={isLookingUp || !employeeId.trim()}
              style={{ fontSize: 12, background: 'none', border: 'none', color: '#0284c7', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 500 }}
            >
              <RefreshCw size={11} className={isLookingUp ? 'spin-icon' : ''} />
              <span>{isLookingUp ? 'Checking...' : 'Check ID & Send Code'}</span>
            </button>
          </div>
          <div className="auth-input-wrapper">
            <User size={16} className="auth-field-icon" />
            <input
              id="reg-emp-id"
              type="text"
              className="auth-input"
              placeholder="e.g. EMP-1001"
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              required
            />
          </div>
        </div>

        {/* Read-Only Corporate Profile Card */}
        <div className="auth-readonly-card" aria-label="Corporate Directory Record (Read-Only)">
          <div className="auth-readonly-header">
            <div className="auth-readonly-title-group">
              <Lock size={13} className="auth-readonly-lock-icon" />
              <span className="auth-readonly-title">Corporate Directory Record</span>
            </div>
            <span className="auth-readonly-badge">Auto-Populated • Read Only</span>
          </div>

          <div className="auth-readonly-grid">
            <div className="auth-readonly-item">
              <span className="readonly-item-label">
                <User size={12} />
                <span>Employee Name</span>
              </span>
              <span className="readonly-item-val">{employeeData?.employeeName || '—'}</span>
            </div>

            <div className="auth-readonly-item">
              <span className="readonly-item-label">
                <Mail size={12} />
                <span>Company Email</span>
              </span>
              <span className="readonly-item-val email-highlight">{employeeData?.companyEmail || '—'}</span>
            </div>

            <div className="auth-readonly-item">
              <span className="readonly-item-label">
                <Briefcase size={12} />
                <span>Designation</span>
              </span>
              <span className="readonly-item-val">{employeeData?.designation || '—'}</span>
            </div>

            <div className="auth-readonly-item">
              <span className="readonly-item-label">
                <Building2 size={12} />
                <span>Department</span>
              </span>
              <span className="readonly-item-val">{employeeData?.department || '—'}</span>
            </div>

            <div className="auth-readonly-item span-full">
              <span className="readonly-item-label">
                <MapPin size={12} />
                <span>Operational Site</span>
              </span>
              <span className="readonly-item-val">{employeeData?.operationalSite || '—'}</span>
            </div>
          </div>
        </div>

        {/* OTP Section */}
        <div className="auth-otp-section">
          <div className="auth-otp-header">
            <div className="auth-otp-title-group">
              <KeyRound size={15} className="auth-otp-icon" />
              <span className="auth-otp-title">Email Verification Code</span>
            </div>
            <span className="auth-otp-sent-hint">Company email verification</span>
          </div>
          <p className="auth-supporting-text">
            {employeeData?.companyEmail
              ? `Enter the 6-digit OTP sent to ${employeeData.companyEmail}`
              : 'Enter the 6-digit OTP sent to your registered company email'}
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

        {/* Verify OTP Button */}
        <button
          type="submit"
          className="auth-submit-btn"
          disabled={isVerifying}
          id="verify-otp-btn"
        >
          {isVerifying ? (
            <span>Verifying Corporate Identity...</span>
          ) : (
            <>
              <span>Verify OTP & Continue</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </form>

      {/* Footer Link for Returning Employees */}
      <div className="auth-panel-footer">
        <span className="auth-footer-text">Already registered?</span>
        <button
          type="button"
          className="auth-link-btn"
          onClick={onSwitchToLogin}
          id="reg-to-login-link"
        >
          Login
        </button>
      </div>
    </div>
  );
}
