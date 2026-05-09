import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClinVision AI",
  description: "Medical imaging AI MVP for asynchronous chest X-ray inference"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

