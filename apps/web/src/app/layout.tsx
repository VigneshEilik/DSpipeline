import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ModelOps Studio — Enterprise ML Model-to-Production Platform",
  description: "From Data to Intelligence. From Experiment to Production.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased bg-background text-foreground">
        {children}
      </body>
    </html>
  );
}
