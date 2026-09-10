import React, { useState } from 'react';
import EmployeeVerification from './EmployeeVerification';
import SetPassword from './SetPassword';

export interface RegistrationPanelProps {
  onSwitchToLogin: () => void;
}

export type RegistrationStage = 'verification' | 'setPassword';

export default function RegistrationPanel({
  onSwitchToLogin,
}: RegistrationPanelProps) {
  const [stage, setStage] = useState<RegistrationStage>('verification');

  return (
    <div className="auth-panel registration-panel" aria-label="New employee registration interface">
      <div className="auth-panel-inner">
        {stage === 'verification' ? (
          <EmployeeVerification
            onAdvanceToPassword={() => setStage('setPassword')}
            onSwitchToLogin={onSwitchToLogin}
          />
        ) : (
          <SetPassword
            onBackToVerification={() => setStage('verification')}
            onSwitchToLogin={onSwitchToLogin}
          />
        )}
      </div>
    </div>
  );
}
