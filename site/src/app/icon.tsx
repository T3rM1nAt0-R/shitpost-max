import { ImageResponse } from "next/og";

export const dynamic = "force-static";
export const size = { width: 32, height: 32 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #ff00aa, #ffd700)",
          borderRadius: 8,
          color: "#000",
          fontSize: 26,
          fontWeight: 900,
        }}
      >
        $
      </div>
    ),
    size,
  );
}
