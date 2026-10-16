const MAX_SCREENSHOT_BYTES = 10 * 1024 * 1024;
const ALLOWED_SCREENSHOT_TYPES = new Set(['image/png', 'image/jpeg', 'image/webp']);

export async function extractScreenshotText(
  file: File,
  onProgress?: (progress: number) => void,
): Promise<string> {
  if (!ALLOWED_SCREENSHOT_TYPES.has(file.type)) {
    throw new Error('Choose a PNG, JPG, JPEG, or WEBP image.');
  }
  if (file.size > MAX_SCREENSHOT_BYTES) {
    throw new Error('The screenshot must be 10 MB or smaller.');
  }
  const { recognize } = await import('tesseract.js');
  const result = await recognize(file, 'eng', {
    logger: message => {
      if (message.status === 'recognizing text' && typeof message.progress === 'number') {
        onProgress?.(Math.round(message.progress * 100));
      }
    },
  });
  const text = result.data.text.replace(/\s+/g, ' ').trim();
  if (text.length < 3) {
    throw new Error('Guard could not read enough text from this image. Try a clearer screenshot or paste the text manually.');
  }
  return text.slice(0, 20000);
}
