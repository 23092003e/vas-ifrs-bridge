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
});

export const metadata: Metadata = {
	title: "VAS·IFRS Knowledge Engine",
	description:
		"AI-powered accounting standards assistant for Vietnamese Accounting Standards and IFRS",
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
				style={{ height: "100%", margin: 0, overflow: "hidden" }}
			>
				{children}
			</body>
		</html>
	);
}
