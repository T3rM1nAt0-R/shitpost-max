import type { Metadata, Viewport } from "next";
import { Bungee, Space_Grotesk } from "next/font/google";
import { CrtOverlay, GradientBlobs } from "@/components/fx/Backdrop";
import BillionaireMode from "@/components/fx/BillionaireMode";
import CursorTrail from "@/components/fx/CursorTrail";
import NavBar from "@/components/fx/NavBar";
import NewsTicker from "@/components/fx/NewsTicker";
import PageTransition from "@/components/fx/PageTransition";
import ParticleField from "@/components/fx/ParticleField";
import "./globals.css";

const display = Bungee({
  variable: "--font-display",
  weight: "400",
  subsets: ["latin"],
  display: "swap",
});

const body = Space_Grotesk({
  variable: "--font-body",
  subsets: ["latin"],
  display: "swap",
});

const DESCRIPTION =
  "I didn't build this website. I acquired the concept of websites and fired it until it got 1000000x better. SHITPOSTMAX: hyperscale engineering for problems that don't exist, funded by vibes and a rocket I bought on a whim.";

export const metadata: Metadata = {
  metadataBase: new URL("https://shitpostmax.com"),
  title: {
    default: "SHITPOSTMAX — 1000000x Engineering for Problems That Don't Exist",
    template: "%s | SHITPOSTMAX",
  },
  description: DESCRIPTION,
  applicationName: "SHITPOSTMAX",
  openGraph: {
    type: "website",
    url: "/",
    siteName: "SHITPOSTMAX",
    title: "SHITPOSTMAX — 1000000x Engineering for Problems That Don't Exist",
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: "SHITPOSTMAX — 1000000x Engineering for Problems That Don't Exist",
    description: DESCRIPTION,
  },
  appleWebApp: {
    capable: true,
    title: "SHITPOSTMAX",
    statusBarStyle: "black-translucent",
  },
};

export const viewport: Viewport = {
  themeColor: "#000000",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable} h-full antialiased`}>
      <body className="relative flex min-h-full flex-col pt-8">
        <GradientBlobs />
        <ParticleField />
        <NewsTicker />
        <NavBar />
        <PageTransition>{children}</PageTransition>
        <BillionaireMode />
        <CursorTrail />
        <CrtOverlay />
      </body>
    </html>
  );
}
