// ==============================================================================
// KRIYA Frontend API: Settings & Air-Gap Connectivity
// ==============================================================================

const RAW_BACKEND_URL: string = import.meta.env.VITE_BACKEND_URL || '';
const BACKEND_URL = RAW_BACKEND_URL.replace(/\/+$/, '');

export interface InternetStatus {
  enabled: boolean;
  firewall_enforced: boolean;
}

/**
 * Fetches the current outbound internet connectivity status from backend.
 */
export async function getInternetStatus(): Promise<InternetStatus> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/settings/internet`);
    if (!res.ok) {
      throw new Error(`Failed to fetch internet status: ${res.statusText}`);
    }
    return await res.json();
  } catch (error) {
    console.warn('[Settings API] Could not fetch internet status:', error);
    return { enabled: false, firewall_enforced: false };
  }
}

/**
 * Toggles outbound internet services for web search and package downloads.
 */
export async function toggleInternet(enabled: boolean): Promise<InternetStatus> {
  const res = await fetch(`${BACKEND_URL}/api/settings/internet/toggle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ enabled }),
  });

  if (!res.ok) {
    throw new Error(`Failed to toggle internet: ${res.statusText}`);
  }

  return await res.json();
}
