import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import { ToastHost } from "@/components/ToastHost";
import "./globals.css";

const sans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-ibm-sans",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-ibm-mono",
  display: "swap",
});

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
    <html lang="en" className={`${sans.variable} ${mono.variable} h-full`}>
      <body className="min-h-full font-sans antialiased">
        {children}
        <ToastHost />
      </body>
    </html>
  );
}
