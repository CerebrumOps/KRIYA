/**
 * Robust Clipboard Utility
 * Handles modern navigator.clipboard.writeText with graceful fallback to
 * document.execCommand('copy') for non-secure contexts, iframe environments,
 * and background focus states.
 */

export async function copyTextToClipboard(text: string): Promise<boolean> {
  if (text === undefined || text === null) {
    return false;
  }

  const cleanText = typeof text === 'string' ? text : String(text);
  if (!cleanText) {
    return false;
  }

  // Strategy 1: Modern asynchronous Clipboard API (navigator.clipboard)
  if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(cleanText);
      return true;
    } catch (apiErr) {
      console.warn('navigator.clipboard.writeText failed, attempting execCommand fallback:', apiErr);
    }
  }

  // Strategy 2: Universal document.execCommand('copy') with off-screen textarea
  try {
    const textArea = document.createElement('textarea');
    textArea.value = cleanText;

    // Position outside visible screen without triggering scroll
    textArea.style.position = 'fixed';
    textArea.style.top = '-9999px';
    textArea.style.left = '-9999px';
    textArea.style.width = '2em';
    textArea.style.height = '2em';
    textArea.style.padding = '0';
    textArea.style.border = 'none';
    textArea.style.outline = 'none';
    textArea.style.boxShadow = 'none';
    textArea.style.background = 'transparent';
    textArea.style.opacity = '0';
    textArea.setAttribute('readonly', '');

    document.body.appendChild(textArea);

    // Select text content
    textArea.focus({ preventScroll: true });
    textArea.select();
    textArea.setSelectionRange(0, cleanText.length);

    const successful = document.execCommand('copy');
    document.body.removeChild(textArea);

    if (successful) {
      return true;
    }
  } catch (domErr) {
    console.error('document.execCommand fallback copy failed:', domErr);
  }

  return false;
}
