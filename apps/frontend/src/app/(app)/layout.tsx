"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { useEffect, useState } from "react";

export type SidebarState = "expanded" | "collapsed" | "hidden";
export type Theme = "light" | "dark";
export type Palette = "slate" | "bordeaux" | "forest" | "graphite";
export type Density = "compact" | "comfortable" | "spacious";

export default function AppLayout({ children }: { children: React.ReactNode }) {
	const [theme, setTheme] = useState<Theme>("light");
	const [palette, setPalette] = useState<Palette>("slate");
	const [density, setDensity] = useState<Density>("comfortable");
	const [sidebarState, setSidebarState] = useState<SidebarState>("expanded");

	useEffect(() => {
		try {
			const savedTheme = localStorage.getItem("vas-theme") as Theme | null;
			if (savedTheme && (savedTheme === "light" || savedTheme === "dark")) {
				setTheme(savedTheme);
			}
			const savedPalette = localStorage.getItem(
				"vas-palette",
			) as Palette | null;
			if (
				savedPalette &&
				["slate", "bordeaux", "forest", "graphite"].includes(savedPalette)
			) {
				setPalette(savedPalette);
			}
			const savedDensity = localStorage.getItem(
				"vas-density",
			) as Density | null;
			if (
				savedDensity &&
				["compact", "comfortable", "spacious"].includes(savedDensity)
			) {
				setDensity(savedDensity);
			}
		} catch {
			// Ignore localStorage error in private mode
		}
	}, []);

	const handleToggleTheme = () => {
		setTheme((prev) => {
			const next = prev === "light" ? "dark" : "light";
			try {
				localStorage.setItem("vas-theme", next);
			} catch {}
			return next;
		});
	};

	const handleSelectPalette = (newPalette: Palette) => {
		setPalette(newPalette);
		try {
			localStorage.setItem("vas-palette", newPalette);
		} catch {}
	};

	const handleSelectDensity = (newDensity: Density) => {
		setDensity(newDensity);
		try {
			localStorage.setItem("vas-density", newDensity);
		} catch {}
	};

	useEffect(() => {
		const handler = () =>
			setSidebarState((s) => (s === "expanded" ? "hidden" : "expanded"));
		window.addEventListener("vas-toggle-sidebar", handler);
		return () => window.removeEventListener("vas-toggle-sidebar", handler);
	}, []);

	return (
		<div
			className="app"
			data-sidebar={sidebarState}
			data-theme={theme}
			data-density={density}
			{...(palette !== "slate" ? { "data-palette": palette } : {})}
		>
			<Sidebar
				theme={theme}
				onToggleTheme={handleToggleTheme}
				palette={palette}
				onSelectPalette={handleSelectPalette}
				density={density}
				onSelectDensity={handleSelectDensity}
				onNewChat={() => window.dispatchEvent(new CustomEvent("vas-new-chat"))}
			/>
			<main className="main">{children}</main>
		</div>
	);
}
