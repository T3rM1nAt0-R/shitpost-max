import Feed from "@/components/feed/Feed";
import Footer from "@/components/feed/Footer";
import Hero from "@/components/feed/Hero";
import Stats from "@/components/feed/Stats";
import Ticker from "@/components/feed/Ticker";

export default function Home() {
  return (
    <div
      className="relative min-h-screen overflow-x-hidden text-white"
      style={{
        backgroundImage:
          "radial-gradient(circle at 20% 0%, rgba(217,70,239,0.18), transparent 40%), radial-gradient(circle at 80% 30%, rgba(34,211,238,0.14), transparent 40%), linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
        backgroundSize: "auto, auto, 40px 40px, 40px 40px",
      }}
    >
      <div className="flex-1">
        <Hero />
        <Ticker />
        <Stats />
        <Feed />
      </div>
      <Footer />
    </div>
  );
}
