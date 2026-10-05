import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #000 0%, #ff00aa 60%, #ffd700 100%)",
          color: "#fff",
          fontWeight: 900,
        }}
      >
        <div style={{ display: "flex", fontSize: 110, lineHeight: 1 }}>$</div>
        <div style={{ display: "flex", fontSize: 30, letterSpacing: 2 }}>SPM</div>
      </div>
    ),
    size,
  );
}
