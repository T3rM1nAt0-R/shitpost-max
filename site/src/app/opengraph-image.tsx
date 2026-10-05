import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const alt = "SHITPOSTMAX - the fanciest, most shitposty website ever";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
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
          background:
            "radial-gradient(circle at 20% 20%, #ff00aa 0%, transparent 45%), radial-gradient(circle at 80% 80%, #00ffea 0%, transparent 45%), #000",
          color: "#fff",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", fontSize: 28, letterSpacing: 12, color: "#ffd700" }}>
          EST. WHENEVER WE FELT LIKE IT
        </div>
        <div
          style={{
            display: "flex",
            fontSize: 150,
            fontWeight: 900,
            letterSpacing: -4,
            marginTop: 10,
            color: "#fff",
            textShadow: "0 0 30px #ff00aa, 0 0 60px #ff00aa",
          }}
        >
          SHITPOSTMAX
        </div>
        <div style={{ display: "flex", fontSize: 40, marginTop: 20, color: "#00ffea" }}>
          The net worth of every billionaire. The maturity of none.
        </div>
        <div
          style={{
            display: "flex",
            marginTop: 40,
            padding: "14px 36px",
            border: "4px solid #ffd700",
            borderRadius: 999,
            fontSize: 32,
            color: "#ffd700",
          }}
        >
          $$$ VALUATION: YES $$$
        </div>
      </div>
    ),
    size,
  );
}
