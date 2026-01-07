import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Virtual Try-On",
  description: "Try on clothes virtually using AI - upload your photo and see how any outfit looks on you",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
