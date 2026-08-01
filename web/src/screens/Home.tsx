import HomeChrome from "../components/HomeChrome";

// Screen 01 -- static baseline, no Concierge involvement at all. Exists so the
// "pixel-identical except one card" claim in docs/differentiation.md #4 is
// checkable: this and Entry.tsx render the exact same HomeChrome.
export default function Home() {
  return <HomeChrome />;
}
