/**
 * KRIYA Frontend - Employee Schemas (TypeScript)
 * Represents backend-provided corporate directory data for employees.
 * Separated from user-entered form inputs and authentication UI state.
 */

export interface Employee {
  employeeId: string;
  employeeName: string;
  companyEmail: string;
  designation: string;
  department: string;
  operationalSite: string;
}
