import { Analytics } from "@vercel/analytics/next";
import { RealtimeDrainSync } from "@/components/realtime-drain-sync";
import { QueryProvider } from "@/components/query-provider";
import { ThemeProvider } from "@/components/theme-provider";
import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const themeInitScript = `
  (function () {
    var storageKey = 'smartdrain-theme-mode';
    var stored = localStorage.getItem(storageKey);
    var mode = stored === 'light' || stored === 'dark' || stored === 'system' ? stored : 'system';
    var resolved = mode === 'system'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : mode;
    var root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolved);
    root.dataset.themeMode = mode;
    root.style.colorScheme = resolved;
  })();
`;

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  applicationName: "SmartDrain",
  title: "SmartDrain | 지능형 도시 침수 관리",
  description:
    "CCTV 스냅샷, 수위·유속 센서 데이터, AI 분석을 결합해 도시 배수 시설의 침수 위험을 실시간으로 모니터링합니다.",
  keywords: [
    "SmartDrain",
    "도시 침수",
    "빗물받이",
    "CCTV 모니터링",
    "침수 위험 관제",
  ],
  icons: {
    icon: {
      url: "/images/metaimage/smartdrain-icon.png",
      type: "image/png",
    },
    apple: {
      url: "/images/metaimage/smartdrain-icon.png",
      type: "image/png",
    },
  },
  openGraph: {
    type: "website",
    locale: "ko_KR",
    siteName: "SmartDrain",
    title: "SmartDrain | 지능형 도시 침수 관리",
    description:
      "CCTV 스냅샷, 수위·유속 센서 데이터, AI 분석을 결합한 도시 배수 시설 침수 위험 관제 서비스입니다.",
    images: [
      {
        url: "/images/metaimage/smartdrain-og-image.png",
        width: 1672,
        height: 941,
        alt: "SmartDrain 도시 침수 모니터링 대시보드",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "SmartDrain | 지능형 도시 침수 관리",
    description:
      "CCTV와 AI 분석으로 도시 배수 시설의 침수 위험을 실시간 관제합니다.",
    images: ["/images/metaimage/smartdrain-og-image.png"],
  },
};

export const viewport: Viewport = {
  colorScheme: "light dark",
  themeColor: "#0e7490",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ko"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} bg-background`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="font-sans antialiased">
        <ThemeProvider>
          <QueryProvider>
            <RealtimeDrainSync />
            {children}
          </QueryProvider>
        </ThemeProvider>
        {process.env.NODE_ENV === "production" && <Analytics />}
      </body>
    </html>
  );
}
