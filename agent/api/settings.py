# ==============================================================================
# KRIYA API: System & Security Settings
# ==============================================================================
# Controls air-gap security parameters and dynamic connectivity toggles:
# 1. Internet Services Toggle: Allows operator to open/close outbound internet
# 2. Firewall enforcement via iptables (with Tailscale 100.x.x.x permanently whitelisted)
# ==============================================================================

import os
import subprocess
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Global state: Default to sovereign air-gapped mode (False)
_internet_enabled: bool = False


class InternetStatusResponse(BaseModel):
    enabled: bool = Field(..., description="Whether outbound internet access is currently active")
    firewall_enforced: bool = Field(..., description="Whether kernel firewall rules were applied")


class ToggleInternetRequest(BaseModel):
    enabled: bool = Field(..., description="Desired internet state: True for enabled, False for air-gapped")


def apply_firewall_policy(enabled: bool) -> bool:
    """
    Applies container kernel firewall policies via iptables.
    Always preserves Tailscale mesh network (100.0.0.0/8) and local loopback.
    Returns True if iptables was successfully invoked, False otherwise.
    """
    # Only attempt iptables if running inside container or as root
    if not (os.path.exists("/.dockerenv") or os.getenv("KRIYA_CONTAINER") == "1" or os.geteuid() == 0 if hasattr(os, "geteuid") else False):
        return False

    try:
        if enabled:
            # Open outbound internet access
            subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], capture_output=True, timeout=3)
            return True
        else:
            # Enforce air-gapped lockdown while preserving Tailscale and local traffic
            subprocess.run(["iptables", "-P", "OUTPUT", "DROP"], capture_output=True, timeout=3)
            subprocess.run(["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], capture_output=True, timeout=3)
            subprocess.run(["iptables", "-A", "OUTPUT", "-d", "127.0.0.0/8", "-j", "ACCEPT"], capture_output=True, timeout=3)
            # Tailscale carrier-grade CGNAT block (100.64.0.0/10)
            subprocess.run(["iptables", "-A", "OUTPUT", "-d", "100.0.0.0/8", "-j", "ACCEPT"], capture_output=True, timeout=3)
            # Docker bridge networks
            subprocess.run(["iptables", "-A", "OUTPUT", "-d", "172.16.0.0/12", "-j", "ACCEPT"], capture_output=True, timeout=3)
            return True
    except Exception:
        return False


def is_internet_enabled() -> bool:
    """Helper for internal tools (e.g. websearch) to inspect internet state."""
    global _internet_enabled
    return _internet_enabled


@router.get("/internet", response_model=InternetStatusResponse)
def get_internet_status():
    """Returns current workbench internet access state."""
    return InternetStatusResponse(
        enabled=_internet_enabled,
        firewall_enforced=True
    )


@router.post("/internet", response_model=InternetStatusResponse)
@router.post("/internet/toggle", response_model=InternetStatusResponse)
def toggle_internet(request: ToggleInternetRequest):
    """Toggles outbound internet access on or off."""
    global _internet_enabled
    _internet_enabled = request.enabled
    applied = apply_firewall_policy(_internet_enabled)
    return InternetStatusResponse(
        enabled=_internet_enabled,
        firewall_enforced=applied
    )
