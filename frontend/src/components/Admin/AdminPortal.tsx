import React, { useState, useEffect, useMemo } from 'react';
import {
  Users,
  UserPlus,
  UserCheck,
  UserX,
  Shield,
  ShieldAlert,
  KeyRound,
  RefreshCw,
  Trash2,
  ArrowLeft,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Building2,
  Cpu,
  HardDrive,
  Network,
  Sun,
  Moon,
  X,
  Lock,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { Employee } from '../../schemas/employee';
import {
  AdminEmployee,
  AdminMetrics,
  EnrollEmployeePayload,
  fetchAdminEmployees,
  fetchAdminStats,
  enrollEmployee,
  deleteEmployee,
  toggleEmployeeActive,
  resetEmployeeRegistration,
} from '../../api/admin_api';
import './AdminPortal.css';

export interface AdminPortalProps {
  onReturnToApp: () => void;
  currentUser: Employee | null;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

const ACCESS_LEVEL_LABELS: Record<string, { label: string; color: string; bg: string; border: string }> = {
  admin: {
    label: 'Root Admin',
    color: '#8b5cf6',
    bg: 'rgba(139, 92, 246, 0.12)',
    border: 'rgba(139, 92, 246, 0.3)',
  },
  lead_engineer: {
    label: 'Lead Engineer',
    color: '#3b82f6',
    bg: 'rgba(59, 130, 246, 0.12)',
    border: 'rgba(59, 130, 246, 0.3)',
  },
  senior_engineer: {
    label: 'Senior Engineer',
    color: '#10b981',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.3)',
  },
  process_engineer: {
    label: 'Process Engineer',
    color: '#06b6d4',
    bg: 'rgba(6, 182, 212, 0.12)',
    border: 'rgba(6, 182, 212, 0.3)',
  },
  technician: {
    label: 'Field Technician',
    color: '#f59e0b',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.3)',
  },
};

const DEFAULT_PERMISSIONS_MAP: Record<string, string[]> = {
  admin: [
    'chat:standard',
    'chat:reasoning',
    'tools:read_telemetry',
    'tools:simulate_process',
    'schematics:view_p_and_id',
    'approvals:approve_plan',
    'admin:manage_employees',
  ],
  lead_engineer: [
    'chat:standard',
    'chat:reasoning',
    'tools:read_telemetry',
    'tools:simulate_process',
    'schematics:view_p_and_id',
    'approvals:approve_plan',
  ],
  senior_engineer: [
    'chat:standard',
    'chat:reasoning',
    'tools:read_telemetry',
    'tools:simulate_process',
    'schematics:view_p_and_id',
  ],
  process_engineer: [
    'chat:standard',
    'chat:reasoning',
    'tools:read_telemetry',
  ],
  technician: [
    'chat:standard',
    'tools:read_telemetry',
  ],
};

const INITIAL_FORM: EnrollEmployeePayload = {
  employeeId: '',
  employeeName: '',
  companyEmail: '',
  designation: 'Process Operations Engineer',
  department: 'Crude Distillation Unit (CDU-II)',
  operationalSite: 'Mangalore Refinery Complex (Site Alpha)',
  accessLevel: 'process_engineer',
  permissions: DEFAULT_PERMISSIONS_MAP['process_engineer'],
};

export default function AdminPortal({
  onReturnToApp,
  currentUser,
  theme,
  onToggleTheme,
}: AdminPortalProps) {
  const [employees, setEmployees] = useState<AdminEmployee[]>([]);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [airGap, setAirGap] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'registered' | 'pending' | 'active' | 'suspended'>('all');
  const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // Enroll Form State
  const [formData, setFormData] = useState<EnrollEmployeePayload>(INITIAL_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmittingEnroll, setIsSubmittingEnroll] = useState(false);

  // Confirm deletion dialog state
  const [confirmDeleteEmp, setConfirmDeleteEmp] = useState<AdminEmployee | null>(null);

  // Auto-dismiss toast
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4000);
    return () => clearTimeout(t);
  }, [toast]);

  // Load directory and stats
  const loadData = async () => {
    setIsLoading(true);
    try {
      const [empList, statsRes] = await Promise.all([
        fetchAdminEmployees(),
        fetchAdminStats(),
      ]);
      setEmployees(empList);
      setMetrics(statsRes.metrics);
      setAirGap(statsRes.airGapStatus);
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to load administrative data.' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filtered employees list
  const filteredEmployees = useMemo(() => {
    return employees.filter((emp) => {
      // Search matching
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        emp.employee_id.toLowerCase().includes(q) ||
        emp.employee_name.toLowerCase().includes(q) ||
        emp.company_email.toLowerCase().includes(q) ||
        emp.designation.toLowerCase().includes(q) ||
        emp.department.toLowerCase().includes(q) ||
        emp.operational_site.toLowerCase().includes(q);

      if (!matchesSearch) return false;

      // Status filter
      if (statusFilter === 'registered') return emp.is_registered;
      if (statusFilter === 'pending') return !emp.is_registered;
      if (statusFilter === 'active') return emp.is_active;
      if (statusFilter === 'suspended') return !emp.is_active;

      return true;
    });
  }, [employees, searchQuery, statusFilter]);

  // Handle access level change in enroll form
  const handleRoleChange = (role: string) => {
    setFormData((prev) => ({
      ...prev,
      accessLevel: role,
      permissions: DEFAULT_PERMISSIONS_MAP[role] || DEFAULT_PERMISSIONS_MAP['process_engineer'],
    }));
  };

  // Toggle permission in enroll form
  const handlePermissionToggle = (perm: string) => {
    setFormData((prev) => {
      const current = prev.permissions || [];
      const updated = current.includes(perm)
        ? current.filter((p) => p !== perm)
        : [...current, perm];
      return { ...prev, permissions: updated };
    });
  };

  // Submit enrollment
  const handleEnrollSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const empId = formData.employeeId.trim().toUpperCase();
    if (!empId) {
      setFormError('Employee ID is required.');
      return;
    }
    if (!/^(EMP|ADMIN)-\d{3,6}$/i.test(empId)) {
      setFormError('Employee ID must follow corporate format (e.g. EMP-2045 or ADMIN-1001).');
      return;
    }
    if (!formData.employeeName.trim()) {
      setFormError('Full Employee Name is required.');
      return;
    }
    if (!formData.companyEmail.trim() || !formData.companyEmail.includes('@')) {
      setFormError('Valid corporate email address is required.');
      return;
    }

    setIsSubmittingEnroll(true);
    try {
      await enrollEmployee({
        ...formData,
        employeeId: empId,
        companyEmail: formData.companyEmail.trim().toLowerCase(),
      });
      setToast({
        type: 'success',
        message: `Employee ${empId} successfully enrolled! They can now register via OTP verification.`,
      });
      setIsEnrollModalOpen(false);
      setFormData(INITIAL_FORM);
      await loadData();
    } catch (err: any) {
      setFormError(err.message || 'Failed to enroll employee.');
    } finally {
      setIsSubmittingEnroll(false);
    }
  };

  // Toggle Active/Suspended
  const handleToggleActive = async (emp: AdminEmployee) => {
    setActionLoadingId(emp.employee_id);
    try {
      const res = await toggleEmployeeActive(emp.employee_id);
      setToast({
        type: 'info',
        message: `Employee ${emp.employee_id} is now ${res.isActive ? 'Active' : 'Suspended'}.`,
      });
      setEmployees((prev) =>
        prev.map((e) =>
          e.employee_id === emp.employee_id ? { ...e, is_active: res.isActive } : e
        )
      );
      if (metrics) {
        setMetrics({
          ...metrics,
          activeEmployees: res.isActive ? metrics.activeEmployees + 1 : metrics.activeEmployees - 1,
          suspendedEmployees: res.isActive ? metrics.suspendedEmployees - 1 : metrics.suspendedEmployees + 1,
        });
      }
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to update account status.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  // Reset registration
  const handleResetRegistration = async (emp: AdminEmployee) => {
    if (!window.confirm(`Reset credentials for ${emp.employee_name} (${emp.employee_id})?\n\nThis will clear their password and active sessions, allowing them to re-register with OTP.`)) {
      return;
    }

    setActionLoadingId(emp.employee_id);
    try {
      await resetEmployeeRegistration(emp.employee_id);
      setToast({
        type: 'success',
        message: `Registration reset for ${emp.employee_id}. Credentials cleared for re-onboarding.`,
      });
      setEmployees((prev) =>
        prev.map((e) =>
          e.employee_id === emp.employee_id ? { ...e, is_registered: false } : e
        )
      );
      if (metrics && emp.is_registered) {
        setMetrics({
          ...metrics,
          registeredEmployees: metrics.registeredEmployees - 1,
          pendingRegistration: metrics.pendingRegistration + 1,
        });
      }
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to reset registration.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  // Delete employee
  const handleConfirmDelete = async () => {
    if (!confirmDeleteEmp) return;
    const targetId = confirmDeleteEmp.employee_id;
    setActionLoadingId(targetId);
    try {
      await deleteEmployee(targetId);
      setToast({
        type: 'success',
        message: `Employee ${targetId} permanently removed from corporate directory.`,
      });
      setEmployees((prev) => prev.filter((e) => e.employee_id !== targetId));
      setConfirmDeleteEmp(null);
      await loadData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to delete employee.' });
    } finally {
      setActionLoadingId(null);
    }
  };

  return (
    <div className="admin-portal-root">
      {/* Toast Notification */}
      {toast && (
        <div className={`admin-toast admin-toast-${toast.type}`} role="status">
          {toast.type === 'success' && <CheckCircle2 size={16} />}
          {toast.type === 'error' && <AlertCircle size={16} />}
          {toast.type === 'info' && <AlertTriangle size={16} />}
          <span>{toast.message}</span>
          <button type="button" className="admin-toast-close" onClick={() => setToast(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Top Sovereign Bar */}
      <header className="admin-header">
        <div className="admin-header-left">
          <button
            type="button"
            className="admin-back-btn"
            onClick={onReturnToApp}
            title="Return to Sovereign AI Workbench"
          >
            <ArrowLeft size={16} />
            <span>Return to Workbench</span>
          </button>

          <div className="admin-title-group">
            <div className="admin-emblem">
              <Shield size={18} />
            </div>
            <div>
              <h1 className="admin-title">Sovereign Directory & Personnel Administration</h1>
              <p className="admin-subtitle">
                Air-Gapped Access Control, Corporate ID Enrollment, and Security Governance
              </p>
            </div>
          </div>
        </div>

        <div className="admin-header-right">
          <div className="admin-badge-airgap">
            <div className="admin-pulse-dot" />
            <span>Mesh: Sovereign Air-Gap</span>
          </div>

          {currentUser && (
            <div className="admin-user-pill">
              <span className="admin-role-tag">Admin</span>
              <span>{currentUser.employeeName} ({currentUser.employeeId})</span>
            </div>
          )}

          <button
            type="button"
            className="admin-icon-btn"
            onClick={onToggleTheme}
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>

          <button
            type="button"
            className="admin-icon-btn"
            onClick={loadData}
            title="Refresh Directory"
          >
            <RefreshCw size={17} className={isLoading ? 'admin-spin' : ''} />
          </button>
        </div>
      </header>

      {/* Main Admin Content Container */}
      <main className="admin-container">
        {/* KPI Metrics Strip */}
        <section className="admin-metrics-grid" aria-label="System Metrics">
          <div className="admin-metric-card">
            <div className="admin-metric-icon-wrap" style={{ color: '#10D687', background: 'rgba(16, 214, 135, 0.12)' }}>
              <Users size={20} />
            </div>
            <div className="admin-metric-content">
              <span className="admin-metric-label">Enrolled Personnel</span>
              <span className="admin-metric-value">{metrics?.totalEmployees ?? '—'}</span>
            </div>
          </div>

          <div className="admin-metric-card">
            <div className="admin-metric-icon-wrap" style={{ color: '#10b981', background: 'rgba(16, 185, 129, 0.12)' }}>
              <UserCheck size={20} />
            </div>
            <div className="admin-metric-content">
              <span className="admin-metric-label">Registered / Active</span>
              <span className="admin-metric-value">
                {metrics ? `${metrics.registeredEmployees} / ${metrics.activeEmployees}` : '—'}
              </span>
            </div>
          </div>

          <div className="admin-metric-card">
            <div className="admin-metric-icon-wrap" style={{ color: '#f59e0b', background: 'rgba(245, 158, 11, 0.12)' }}>
              <KeyRound size={20} />
            </div>
            <div className="admin-metric-content">
              <span className="admin-metric-label">Pending Onboarding</span>
              <span className="admin-metric-value">{metrics?.pendingRegistration ?? '—'}</span>
            </div>
          </div>

          <div className="admin-metric-card">
            <div className="admin-metric-icon-wrap" style={{ color: '#8b5cf6', background: 'rgba(139, 92, 246, 0.12)' }}>
              <ShieldAlert size={20} />
            </div>
            <div className="admin-metric-content">
              <span className="admin-metric-label">Admin Accounts</span>
              <span className="admin-metric-value">{metrics?.adminCount ?? '—'}</span>
            </div>
          </div>

          <div className="admin-metric-card">
            <div className="admin-metric-icon-wrap" style={{ color: '#06b6d4', background: 'rgba(6, 182, 212, 0.12)' }}>
              <Building2 size={20} />
            </div>
            <div className="admin-metric-content">
              <span className="admin-metric-label">Refinery Units</span>
              <span className="admin-metric-value">{metrics?.refineryUnits ?? '—'}</span>
            </div>
          </div>
        </section>

        {/* Action Controls Bar */}
        <section className="admin-controls-bar">
          <div className="admin-search-wrap">
            <Search size={16} className="admin-search-icon" />
            <input
              type="text"
              placeholder="Search by Employee ID, Name, Email, or Department..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="admin-search-input"
            />
            {searchQuery && (
              <button
                type="button"
                className="admin-search-clear"
                onClick={() => setSearchQuery('')}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="admin-filters-group">
            <div className="admin-filter-pill-wrap">
              <Filter size={14} />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="admin-filter-select"
              >
                <option value="all">All Personnel ({employees.length})</option>
                <option value="registered">Registered Only</option>
                <option value="pending">Pending Onboarding</option>
                <option value="active">Active Only</option>
                <option value="suspended">Suspended Only</option>
              </select>
            </div>

            <button
              type="button"
              className="admin-primary-cta"
              onClick={() => {
                setFormData(INITIAL_FORM);
                setFormError(null);
                setIsEnrollModalOpen(true);
              }}
            >
              <UserPlus size={16} />
              <span>Enroll New Employee ID</span>
            </button>
          </div>
        </section>

        {/* Directory Table */}
        <section className="admin-table-container">
          <div className="admin-table-header-row">
            <div className="admin-col-emp">Employee & ID</div>
            <div className="admin-col-email">Company Email</div>
            <div className="admin-col-unit">Department & Site</div>
            <div className="admin-col-role">Access Level</div>
            <div className="admin-col-status">Onboarding</div>
            <div className="admin-col-state">Account State</div>
            <div className="admin-col-actions">Management Actions</div>
          </div>

          {isLoading ? (
            <div className="admin-table-loading">
              <RefreshCw size={24} className="admin-spin" />
              <span>Loading Sovereign Directory...</span>
            </div>
          ) : filteredEmployees.length === 0 ? (
            <div className="admin-table-empty">
              <Users size={32} />
              <p>No employees match the specified criteria.</p>
              {searchQuery && (
                <button
                  type="button"
                  className="admin-secondary-btn"
                  onClick={() => {
                    setSearchQuery('');
                    setStatusFilter('all');
                  }}
                >
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div className="admin-table-body">
              {filteredEmployees.map((emp) => {
                const roleBadge = ACCESS_LEVEL_LABELS[emp.access_level] || ACCESS_LEVEL_LABELS['process_engineer'];
                const isSelf = emp.employee_id === currentUser?.employeeId;
                const isRoot = emp.employee_id === 'EMP-0001' || emp.employee_id === 'ADMIN-1001';
                const isActionBusy = actionLoadingId === emp.employee_id;

                return (
                  <div key={emp.employee_id} className={`admin-table-row ${!emp.is_active ? 'row-suspended' : ''}`}>
                    {/* Col 1: Employee ID & Name */}
                    <div className="admin-col-emp">
                      <div className="admin-emp-avatar">
                        {emp.employee_name
                          .split(' ')
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join('')
                          .toUpperCase()}
                      </div>
                      <div className="admin-emp-meta">
                        <span className="admin-emp-name">
                          {emp.employee_name}
                          {isSelf && <span className="admin-you-tag">YOU</span>}
                          {isRoot && <span className="admin-root-tag">ROOT</span>}
                        </span>
                        <span className="admin-emp-id">{emp.employee_id}</span>
                        <span className="admin-emp-desig">{emp.designation}</span>
                      </div>
                    </div>

                    {/* Col 2: Email */}
                    <div className="admin-col-email">
                      <span className="admin-text-email">{emp.company_email}</span>
                    </div>

                    {/* Col 3: Department & Site */}
                    <div className="admin-col-unit">
                      <span className="admin-unit-name">{emp.department}</span>
                      <span className="admin-site-name">{emp.operational_site}</span>
                    </div>

                    {/* Col 4: Access Level */}
                    <div className="admin-col-role">
                      <span
                        className="admin-role-badge"
                        style={{
                          color: roleBadge.color,
                          backgroundColor: roleBadge.bg,
                          borderColor: roleBadge.border,
                        }}
                      >
                        {roleBadge.label}
                      </span>
                    </div>

                    {/* Col 5: Onboarding Status */}
                    <div className="admin-col-status">
                      {emp.is_registered ? (
                        <span className="admin-status-badge badge-registered" title="Password and 2FA configured">
                          <CheckCircle2 size={13} />
                          <span>Registered</span>
                        </span>
                      ) : (
                        <span className="admin-status-badge badge-pending" title="Enrolled ID ready for onboarding">
                          <KeyRound size={13} />
                          <span>Pending OTP</span>
                        </span>
                      )}
                    </div>

                    {/* Col 6: Account State */}
                    <div className="admin-col-state">
                      {emp.is_active ? (
                        <span className="admin-state-pill state-active">Active</span>
                      ) : (
                        <span className="admin-state-pill state-suspended">Suspended</span>
                      )}
                    </div>

                    {/* Col 7: Actions */}
                    <div className="admin-col-actions">
                      {/* Toggle Active / Suspended */}
                      <button
                        type="button"
                        className={`admin-action-btn ${emp.is_active ? 'btn-warn' : 'btn-activate'}`}
                        onClick={() => handleToggleActive(emp)}
                        disabled={isSelf || isRoot || isActionBusy}
                        title={
                          isSelf || isRoot
                            ? 'Cannot suspend root/active administrator'
                            : emp.is_active
                            ? 'Suspend employee access'
                            : 'Re-activate employee account'
                        }
                      >
                        {emp.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                        <span>{emp.is_active ? 'Suspend' : 'Activate'}</span>
                      </button>

                      {/* Reset Registration */}
                      <button
                        type="button"
                        className="admin-action-btn btn-reset"
                        onClick={() => handleResetRegistration(emp)}
                        disabled={isActionBusy}
                        title="Clear credentials and allow employee to re-register via OTP"
                      >
                        <RefreshCw size={14} />
                        <span>Reset</span>
                      </button>

                      {/* Delete ID */}
                      <button
                        type="button"
                        className="admin-action-btn btn-delete"
                        onClick={() => setConfirmDeleteEmp(emp)}
                        disabled={isSelf || isRoot || isActionBusy}
                        title={
                          isSelf || isRoot
                            ? 'Cannot delete root/active administrator'
                            : 'Permanently remove from directory'
                        }
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {/* ENROLL EMPLOYEE MODAL */}
      {isEnrollModalOpen && (
        <div className="admin-modal-backdrop" onClick={() => setIsEnrollModalOpen(false)}>
          <div
            className="admin-modal-panel"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="Enroll New Corporate Employee"
          >
            <div className="admin-modal-header">
              <div className="admin-modal-title-wrap">
                <div className="admin-modal-icon">
                  <UserPlus size={20} />
                </div>
                <div>
                  <h2 className="admin-modal-title">Enroll New Employee ID</h2>
                  <p className="admin-modal-desc">
                    Register a corporate ID into the directory. Personnel can then complete 2FA verification to set their credentials.
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="admin-modal-close"
                onClick={() => setIsEnrollModalOpen(false)}
              >
                <X size={18} />
              </button>
            </div>

            {formError && (
              <div className="admin-modal-error">
                <AlertCircle size={16} />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleEnrollSubmit} className="admin-modal-form">
              <div className="admin-form-row">
                <div className="admin-form-field">
                  <label className="admin-label">
                    Employee ID <span className="req">*</span>
                  </label>
                  <input
                    type="text"
                    className="admin-input"
                    placeholder="e.g. EMP-2045 or ADMIN-1001"
                    value={formData.employeeId}
                    onChange={(e) => setFormData({ ...formData, employeeId: e.target.value })}
                    required
                  />
                  <span className="admin-field-hint">Standard format: EMP-XXXX or ADMIN-XXXX</span>
                </div>

                <div className="admin-form-field">
                  <label className="admin-label">
                    Full Legal Name <span className="req">*</span>
                  </label>
                  <input
                    type="text"
                    className="admin-input"
                    placeholder="e.g. Dr. Rajiv Menon"
                    value={formData.employeeName}
                    onChange={(e) => setFormData({ ...formData, employeeName: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="admin-form-row">
                <div className="admin-form-field">
                  <label className="admin-label">
                    Corporate Email <span className="req">*</span>
                  </label>
                  <input
                    type="email"
                    className="admin-input"
                    placeholder="e.g. rajiv.menon@mrpl.co.in"
                    value={formData.companyEmail}
                    onChange={(e) => setFormData({ ...formData, companyEmail: e.target.value })}
                    required
                  />
                  <span className="admin-field-hint">OTP verification will be dispatched here</span>
                </div>

                <div className="admin-form-field">
                  <label className="admin-label">Job Designation</label>
                  <input
                    type="text"
                    className="admin-input"
                    placeholder="e.g. Senior Reliability Engineer"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                  />
                </div>
              </div>

              <div className="admin-form-row">
                <div className="admin-form-field">
                  <label className="admin-label">Assigned Department</label>
                  <input
                    type="text"
                    className="admin-input"
                    placeholder="e.g. Fluid Catalytic Cracking Unit (FCCU)"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                  />
                </div>

                <div className="admin-form-field">
                  <label className="admin-label">Operational Site</label>
                  <input
                    type="text"
                    className="admin-input"
                    placeholder="e.g. Mangalore Refinery Complex (Site Alpha)"
                    value={formData.operationalSite}
                    onChange={(e) => setFormData({ ...formData, operationalSite: e.target.value })}
                  />
                </div>
              </div>

              <div className="admin-form-field">
                <label className="admin-label">Sovereign Access Level</label>
                <div className="admin-role-selector-grid">
                  {Object.entries(ACCESS_LEVEL_LABELS).map(([key, config]) => (
                    <button
                      key={key}
                      type="button"
                      className={`admin-role-card ${formData.accessLevel === key ? 'selected' : ''}`}
                      onClick={() => handleRoleChange(key)}
                    >
                      <div className="admin-role-card-header">
                        <span
                          className="admin-role-dot"
                          style={{ backgroundColor: config.color }}
                        />
                        <span className="admin-role-card-name">{config.label}</span>
                      </div>
                      <span className="admin-role-card-desc">
                        {key === 'admin' && 'Full directory & system controls'}
                        {key === 'lead_engineer' && 'Approve plans & execute sandbox tools'}
                        {key === 'senior_engineer' && 'Process simulation & P&ID access'}
                        {key === 'process_engineer' && 'Standard AI telemetry & chat'}
                        {key === 'technician' && 'Telemetry read & guided workflows'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="admin-form-field">
                <label className="admin-label">Granular Permission Scopes</label>
                <div className="admin-perms-grid">
                  {[
                    { id: 'chat:standard', label: 'Standard AI Chat' },
                    { id: 'chat:reasoning', label: 'Deep Reasoning Mode' },
                    { id: 'tools:read_telemetry', label: 'Read Refinery Telemetry' },
                    { id: 'tools:simulate_process', label: 'Execute Sandbox Simulations' },
                    { id: 'schematics:view_p_and_id', label: 'View Confidential P&ID Diagrams' },
                    { id: 'approvals:approve_plan', label: 'Approve Execution Plans' },
                    { id: 'admin:manage_employees', label: 'Manage Personnel Directory' },
                  ].map((p) => {
                    const isChecked = (formData.permissions || []).includes(p.id);
                    return (
                      <label key={p.id} className="admin-perm-checkbox-item">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => handlePermissionToggle(p.id)}
                        />
                        <span>{p.label}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="admin-modal-actions">
                <button
                  type="button"
                  className="admin-secondary-btn"
                  onClick={() => setIsEnrollModalOpen(false)}
                  disabled={isSubmittingEnroll}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="admin-primary-cta"
                  disabled={isSubmittingEnroll}
                >
                  {isSubmittingEnroll ? (
                    <>
                      <RefreshCw size={15} className="admin-spin" />
                      <span>Enrolling...</span>
                    </>
                  ) : (
                    <>
                      <UserPlus size={15} />
                      <span>Enroll Employee</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* CONFIRM DELETE DIALOG */}
      {confirmDeleteEmp && (
        <div className="admin-modal-backdrop" onClick={() => setConfirmDeleteEmp(null)}>
          <div
            className="admin-modal-panel admin-confirm-dialog"
            onClick={(e) => e.stopPropagation()}
            role="alertdialog"
          >
            <div className="admin-modal-header">
              <div className="admin-modal-title-wrap">
                <div className="admin-modal-icon icon-danger">
                  <AlertTriangle size={22} />
                </div>
                <div>
                  <h2 className="admin-modal-title">Confirm Employee Removal</h2>
                  <p className="admin-modal-desc">
                    Are you sure you want to remove <strong>{confirmDeleteEmp.employee_name}</strong> (
                    <code>{confirmDeleteEmp.employee_id}</code>) from the corporate directory?
                  </p>
                </div>
              </div>
            </div>

            <p className="admin-delete-warning">
              This action is immediate and cannot be undone. Active sessions for this employee will be invalidated.
            </p>

            <div className="admin-modal-actions">
              <button
                type="button"
                className="admin-secondary-btn"
                onClick={() => setConfirmDeleteEmp(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="admin-danger-btn"
                onClick={handleConfirmDelete}
              >
                <Trash2 size={15} />
                <span>Delete Employee</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
