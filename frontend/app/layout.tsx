import { Analytics } from "@vercel/analytics/next";
import { RealtimeDrainSync } from "@/components/realtime-drain-sync";
import { QueryProvider } from "@/components/query-provider";
import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export const metadata: Metadata = {
    title: "지능형 도시 침수 관리 대시보드",
    description:
        "도시 배수 시설의 CCTV 스냅샷과 센서 데이터를 실시간으로 모니터링하는 관제 대시보드",
    generator: "v0.app",
    icons: {
        icon: [
            {
                url: "/icon-light-32x32.png",
                media: "(prefers-color-scheme: light)",
            },
            {
                url: "/icon-dark-32x32.png",
                media: "(prefers-color-scheme: dark)",
            },
            {
                url: "/icon.svg",
                type: "image/svg+xml",
            },
        ],
        apple: "/apple-icon.png",
    },
};

export const viewport: Viewport = {
    colorScheme: "light dark",
    themeColor: [
        { media: "(prefers-color-scheme: light)", color: "white" },
        { media: "(prefers-color-scheme: dark)", color: "black" },
    ],
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html
            lang="ko"
            className={`${geistSans.variable} ${geistMono.variable} bg-slate-50`}
        >
            <body className="font-sans antialiased">
                <QueryProvider>
                    <RealtimeDrainSync />
                    {children}
                </QueryProvider>
                {process.env.NODE_ENV === "production" && <Analytics />}
            </body>
        </html>
    );
}
