import type { Metadata, Viewport } from "next";
import { Figtree, Instrument_Serif, Spline_Sans_Mono } from "next/font/google";
import { Footer } from "@/components/Footer";
import { SmoothScroll } from "@/components/SmoothScroll";
import { ToastHost } from "@/components/ToastHost";
import "./globals.css";

const display = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  variable: "--font-instrument",
  display: "swap",
});

const sans = Figtree({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-figtree",
  display: "swap",
});

const mono = Spline_Sans_Mono({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-spline",
  display: "swap",
});

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#141A24",
};

export const metadata: Metadata = {
  title: {
    default: "Sentinel",
    template: "%s · Sentinel",
  },
  description:
    "When a database gets sick, Sentinel opens a case, checks what worked last time, and files what it did.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable}`}
    >
      <body className="min-h-full font-sans antialiased">
        <SmoothScroll />
        {children}
        <Footer />
        <ToastHost />
      </body>
    </html>
  );
}
