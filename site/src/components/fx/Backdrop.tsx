/** CSS-only "shader": rainbow conic blobs behind everything. */
export function GradientBlobs() {
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 -z-20 overflow-hidden"
    >
      <span className="fx-blob fx-blob-1" />
      <span className="fx-blob fx-blob-2" />
      <span className="fx-blob fx-blob-3" />
    </div>
  );
}

/** CRT scanlines + film noise on top of everything (subtle, click-through). */
export function CrtOverlay() {
  return <div aria-hidden="true" className="fx-crt pointer-events-none fixed inset-0 z-[70]" />;
}
