import { GeistMono } from "geist/font/mono";
import { GeistSans } from "geist/font/sans";
import type { Metadata } from "next";
import { Newsreader } from "next/font/google";
import "./globals.css";

const newsreader = Newsreader({
	subsets: ["latin"],
	variable: "--font-serif",
	display: "swap",
	weight: ["400", "500", "600", "700"],
	style: ["normal", "italic"],
	adjustFontFallback: false,
});

export const metadata: Metadata = {
	title:
		"VAS-IFRS Bridge — Nền tảng Chuyển đổi & Đối chiếu Chuẩn mực Kế toán Quốc tế",
	description:
		"Cầu nối VAS ↔ IFRS với độ chính xác chuẩn kiểm toán, ứng dụng AI RAG và Knowledge Graph cho doanh nghiệp FDI, tập đoàn niêm yết và hãng kiểm toán.",
};

export default function RootLayout({
	children,
}: { children: React.ReactNode }) {
	return (
		<html
			lang="vi"
			className={`${GeistSans.variable} ${GeistMono.variable} ${newsreader.variable}`}
			style={
				{
					"--font-sans": "var(--font-geist-sans)",
					"--font-mono": "var(--font-geist-mono)",
				} as React.CSSProperties
			}
		>
			<body
				className={`${GeistSans.className} antialiased`}
				style={{ minHeight: "100%", margin: 0 }}
			>
				{children}
			</body>
		</html>
	);
}
