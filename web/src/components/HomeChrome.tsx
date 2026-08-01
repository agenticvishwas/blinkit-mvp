import type { ReactNode } from "react";

// Shared chrome for Screens 01 and 02 -- everything except the one coral
// prompt card is identical between them, per design/mockup.html's caption on
// Screen 02: "nothing existing was touched to add this." Keeping it in one
// component is what makes that claim mechanically true here (Screen 02 can't
// drift from Screen 01 by editing the wrong copy), not just true by
// convention.
export default function HomeChrome({ promptCard }: { promptCard?: ReactNode }) {
  return (
    <div className="flex flex-col h-full bg-app-bg text-ink-900">
      <div className="flex items-center justify-between px-5 pt-3 pb-1 text-xs font-semibold">
        <span>2:51</span>
        <span className="text-ink-500">4G &nbsp; 🔋</span>
      </div>

      <div className="px-5 pb-3">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="text-[10px] font-bold text-coral-600 uppercase tracking-wide">Due to excess demand</div>
            <div className="text-base font-extrabold leading-tight">Delivery in 8 mins</div>
            <div className="text-xs text-ink-500 flex items-center gap-1">
              HOME - B-905, 9th Floor, Tower B <span>▾</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 bg-sand-100 rounded-full px-2 py-1 text-xs font-semibold">
              💰 ₹0
            </div>
            <div className="w-8 h-8 rounded-full bg-sand-200 flex items-center justify-center">👤</div>
          </div>
        </div>

        <div className="flex items-center gap-2 bg-sand-100 rounded-full px-4 py-2.5 text-sm text-ink-500 mb-3">
          🔍 <span className="flex-1">Search "bouquet"</span> 🎤
        </div>

        {promptCard}

        <div className="flex gap-3 overflow-x-auto mb-3 text-[11px] text-center">
          {[
            ["🛍️", "All"],
            ["🪔", "Rakhi"],
            ["🎧", "Electronics"],
            ["💄", "Beauty"],
            ["💊", "Pharmacy"],
            ["🛋️", "Decor"],
          ].map(([icon, label]) => (
            <div key={label} className="flex flex-col items-center gap-1 shrink-0">
              <div className="w-10 h-10 rounded-full bg-sand-100 flex items-center justify-center text-lg">
                {icon}
              </div>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 pb-3">
        <div className="grid grid-cols-2 gap-2.5 mb-3">
          <div className="col-span-2 bg-coral-100 rounded-2xl p-4 relative overflow-hidden">
            <div className="text-sm font-bold">Bands, Cards &amp; Flowers</div>
            <div className="text-xs text-ink-500 line-through">₹199</div>
            <div className="text-lg font-extrabold text-coral-600">₹49</div>
            <div className="absolute right-4 top-4 text-3xl">🌸</div>
          </div>
          {[
            ["🎁", "Gifting Corner"],
            ["🎉", "Party With Friends"],
            ["🍫", "Chocolates & Cakes"],
            ["🌹", "Date Night Edit"],
          ].map(([icon, label]) => (
            <div key={label} className="bg-sand-100 rounded-2xl p-4 flex flex-col justify-between h-24">
              <span className="text-2xl">{icon}</span>
              <span className="text-xs font-semibold">{label}</span>
            </div>
          ))}
        </div>

        <div className="bg-sand-200 rounded-2xl p-4 flex items-center justify-between mb-4">
          <div>
            <div className="text-sm font-bold">In-App Brand Store</div>
            <div className="text-xs text-ink-500">Toys, bags &amp; collectibles</div>
          </div>
          <span>›</span>
        </div>

        <div className="text-sm font-bold mb-2">Frequently bought</div>
        <div className="flex gap-3">
          {[
            { label: "Favourites", more: "+1 more" },
            { label: "Vegetables & Fruits", more: "+15 more" },
          ].map((c) => (
            <div key={c.label} className="bg-sand-100 rounded-2xl p-3 flex-1">
              <div className="flex gap-1 mb-2">
                <div className="w-6 h-6 rounded-md bg-yellow-100" />
                <div className="w-6 h-6 rounded-md bg-green-100" />
                <div className="w-6 h-6 rounded-md bg-sand-300 flex items-center justify-center text-[8px]">
                  {c.more}
                </div>
              </div>
              <div className="text-xs font-semibold">{c.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-canvas-line px-5 py-2 flex justify-between text-[10px] text-ink-500 bg-app-bg">
        {["🏠 Home", "🔁 Order Again", "▦ Categories", "🖨️ Print"].map((t) => (
          <div key={t} className="flex flex-col items-center gap-0.5">
            <span>{t.split(" ")[0]}</span>
            <span>{t.split(" ").slice(1).join(" ")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
