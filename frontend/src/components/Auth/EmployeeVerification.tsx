import React, { useState } from 'react';
import { User, ShieldCheck, Mail, Briefcase, Building2, MapPin, KeyRound, ArrowRight, Lock } from 'lucide-react';
import AuthOtpInput from './AuthOtpInput';
import { Employee } from '../../schemas/employee';

export interface EmployeeVerificationProps {
  onAdvanceToPassword: () => void;
  onSwitchToLogin: () => void;
}

export default function EmployeeVerification({
  onAdvanceToPassword,
  onSwitchToLogin,
}: EmployeeVerificationProps) {
  const [employeeId, setEmployeeId] = useState('');
  const [otp, setOtp] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [employeeData, _setEmployeeData] = useState<Employee | null>(null);

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    // UI demonstration transition to Stage 2
    setTimeout(() => {
      setIsVerifying(false);
      onAdvanceToPassword();
    }, 450);
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

      <form className="auth-form" onSubmit={handleVerify}>
        {/* Editable Employee ID Input */}
        <div className="auth-field-group">
          <label htmlFor="reg-emp-id" className="auth-field-label">
            Assigned Employee ID
          </label>
          <div className="auth-input-wrapper">
            <User size={16} className="auth-field-icon" />
            <input
              id="reg-emp-id"
              type="text"
              className="auth-input"
              placeholder="Enter assigned Employee ID"
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
