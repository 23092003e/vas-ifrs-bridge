"use client";

import {
	type GroupedConversations,
	groupConversations,
	parseConversationsResponse,
} from "@/lib/chat/conversations";
import { createClient } from "@/lib/supabase/client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

/* ── Icons ── */
function MessagesIcon() {
	return (
		<svg
			width="15"
			height="15"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
		</svg>
	);
}

function ArrowsIcon() {
	return (
		<svg
			width="15"
			height="15"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M7 16V4m0 0L3 8m4-4 4 4" />
			<path d="M17 8v12m0 0 4-4m-4 4-4-4" />
		</svg>
	);
}

function FileTextIcon() {
	return (
		<svg
			width="15"
			height="15"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
			<polyline points="14 2 14 8 20 8" />
			<line x1="16" y1="13" x2="8" y2="13" />
			<line x1="16" y1="17" x2="8" y2="17" />
		</svg>
	);
}

function ChartIcon() {
	return (
		<svg
			width="15"
			height="15"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<line x1="18" y1="20" x2="18" y2="10" />
			<line x1="12" y1="20" x2="12" y2="4" />
			<line x1="6" y1="20" x2="6" y2="14" />
		</svg>
	);
}

function LayersIcon() {
	return (
		<svg
			width="15"
			height="15"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<polygon points="12 2 2 7 12 12 22 7 12 2" />
			<polyline points="2 17 12 22 22 17" />
			<polyline points="2 12 12 17 22 12" />
		</svg>
	);
}

function GearIcon() {
	return (
		<svg
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<circle cx="12" cy="12" r="3" />
			<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
		</svg>
	);
}

function SunIcon() {
	return (
		<svg
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<circle cx="12" cy="12" r="5" />
			<line x1="12" y1="1" x2="12" y2="3" />
			<line x1="12" y1="21" x2="12" y2="23" />
			<line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
			<line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
			<line x1="1" y1="12" x2="3" y2="12" />
			<line x1="21" y1="12" x2="23" y2="12" />
			<line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
			<line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
		</svg>
	);
}

function MoonIcon() {
	return (
		<svg
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
		</svg>
	);
}

function ChevronRightIcon({ rotated }: { rotated?: boolean }) {
	return (
		<svg
			width="10"
			height="10"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2.5"
			strokeLinecap="round"
			strokeLinejoin="round"
			style={{
				transform: rotated ? "rotate(90deg)" : "none",
				transition: "transform 200ms",
			}}
		>
			<polyline points="9 18 15 12 9 6" />
		</svg>
	);
}

function SignOutIcon() {
	return (
		<svg
			width="14"
			height="14"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="1.75"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
			<polyline points="16 17 21 12 16 7" />
			<line x1="21" y1="12" x2="9" y2="12" />
		</svg>
	);
}

function TrashIcon() {
	return (
		<svg
			width="12"
			height="12"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
		>
			<polyline points="3 6 5 6 21 6" />
			<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
		</svg>
	);
}

interface SidebarProps {
	onNewChat?: () => void;
	theme: "light" | "dark";
	onToggleTheme: () => void;
}

interface NavItemDef {
	icon: React.ReactNode;
	label: string;
	href: string;
	children?: { label: string; href: string }[];
}

const NAV_ITEMS: NavItemDef[] = [
	{ icon: <MessagesIcon />, label: "Chat", href: "/chat" },
	{ icon: <ArrowsIcon />, label: "Compare", href: "/compare" },
	{
		icon: <LayersIcon />,
		label: "GL Ledger",
		href: "/gl/upload",
		children: [
			{ label: "Upload Trial Balance", href: "/gl/upload" },
			{ label: "Account Mappings", href: "/gl/mappings" },
			{ label: "Adjustments", href: "/gl/adjustments" },
		],
	},
	{ icon: <FileTextIcon />, label: "Documents", href: "/documents" },
	{ icon: <ChartIcon />, label: "Reports", href: "/reports" },
];

export function Sidebar({ onNewChat, theme, onToggleTheme }: SidebarProps) {
	const pathname = usePathname();
	const router = useRouter();
	const [expandedGL, setExpandedGL] = useState(pathname.startsWith("/gl"));
	const [recentSessions, setRecentSessions] = useState<GroupedConversations[]>(
		[],
	);
	const [userProfile, setUserProfile] = useState<{
		name: string;
		email: string;
		role: string;
		workspace: string;
	} | null>(null);

	// Load user profile & workspace metadata
	useEffect(() => {
		let active = true;
		const supabase = createClient();
		void supabase.auth.getUser().then(({ data: { user } }) => {
			if (active && user) {
				const userMetadata = user.user_metadata;
				const appMetadata = user.app_metadata;
				setUserProfile({
					name:
						userMetadata?.full_name ||
						user.email?.split("@")[0] ||
						"Kế toán viên",
					email: user.email || "",
					role:
						typeof appMetadata?.role === "string" ? appMetadata.role : "Member",
					workspace:
						typeof appMetadata?.tenant_name === "string"
							? appMetadata.tenant_name
							: "Shared",
				});
			}
		});
		return () => {
			active = false;
		};
	}, []);

	// Fetch recent conversations
	const fetchConversations = useCallback(async (signal?: AbortSignal) => {
		try {
			const response = await fetch("/api/chat/conversations", { signal });
			if (!response.ok) throw new Error("Failed to load conversations");
			const conversations = parseConversationsResponse(await response.json());
			setRecentSessions(groupConversations(conversations));
		} catch (error) {
			if (!signal?.aborted)
				console.error("Failed to load conversations", error);
		}
	}, []);

	// Fetch conversations on mount or pathname change (when chat starts)
	useEffect(() => {
		const controller = new AbortController();
		void fetchConversations(controller.signal);

		// Event listener for refresh
		const handleRefresh = () => void fetchConversations(controller.signal);
		window.addEventListener("vas-refresh-conversations", handleRefresh);
		return () => {
			controller.abort();
			window.removeEventListener("vas-refresh-conversations", handleRefresh);
		};
	}, [pathname, fetchConversations]);

	const handleDelete = async (e: React.MouseEvent, id: string) => {
		e.preventDefault();
		e.stopPropagation();

		if (!window.confirm("Bạn có chắc chắn muốn xóa cuộc hội thoại này?"))
			return;

		try {
			const res = await fetch(
				`/api/chat/conversations/${encodeURIComponent(id)}`,
				{
					method: "DELETE",
				},
			);
			if (res.ok) {
				await fetchConversations();
				if (pathname === `/chat/${id}`) {
					router.push("/chat");
				}
			}
		} catch (err) {
			console.error(err);
		}
	};

	const handleSignOut = async () => {
		const supabase = createClient();
		await supabase.auth.signOut();
		router.push("/login");
		router.refresh();
	};

	return (
		<aside className="sidebar">
			{/* Brand */}
			<div className="sb-brand">
				<div className="sb-mark">V</div>
				<div className="sb-title">
					<div className="sb-title-1">VAS·IFRS</div>
					<div className="sb-title-2">Knowledge Engine</div>
				</div>
			</div>

			{/* New chat button */}
			<div style={{ padding: "0 var(--sp-3) var(--sp-3)" }}>
				<button type="button" className="sb-new" onClick={onNewChat}>
					<span className="sb-new-plus">+</span>
					<span>Nova tư vấn</span>
					<kbd className="sb-new-kbd">⌘K</kbd>
				</button>
			</div>

			{/* Navigation */}
			<div style={{ flex: 1, overflowY: "auto" }}>
				<div className="sb-section">WORKSPACE</div>
				<nav className="sb-nav">
					{NAV_ITEMS.map((item) => {
						const hasChildren = (item.children?.length ?? 0) > 0;
						const isActive =
							pathname === item.href ||
							(hasChildren && item.children!.some((c) => pathname === c.href));

						return (
							<div key={item.href}>
								{hasChildren ? (
									<button
										type="button"
										className="sb-item"
										data-active={isActive ? "true" : undefined}
										data-expanded={expandedGL ? "true" : undefined}
										onClick={() => setExpandedGL((v) => !v)}
									>
										{item.icon}
										<span>{item.label}</span>
										<span className="sb-chev">
											<ChevronRightIcon rotated={expandedGL} />
										</span>
									</button>
								) : (
									<Link
										href={item.href}
										className="sb-item"
										data-active={isActive ? "true" : undefined}
									>
										{item.icon}
										<span>{item.label}</span>
									</Link>
								)}

								{hasChildren && expandedGL && (
									<div className="sb-sub-nav">
										{item.children!.map((child) => (
											<Link
												key={child.href}
												href={child.href}
												className="sb-sub-item"
												data-active={
													pathname === child.href ? "true" : undefined
												}
											>
												{child.label}
											</Link>
										))}
									</div>
								)}
							</div>
						);
					})}
				</nav>

				{/* Recent sessions */}
				{pathname.startsWith("/chat") && recentSessions.length > 0 && (
					<div className="sb-recent">
						{recentSessions.map((group) => (
							<div key={group.group} className="sb-recent-group">
								<div className="sb-recent-label">{group.group}</div>
								{group.items.map((item) => (
									<div
										key={item.id}
										style={{ position: "relative" }}
										className="sb-recent-item-container"
									>
										<Link
											href={`/chat/${item.id}`}
											className="sb-recent-item"
											data-active={
												pathname === `/chat/${item.id}` ? "true" : undefined
											}
											style={{ paddingRight: "30px", display: "block" }}
										>
											<span
												style={{
													display: "block",
													overflow: "hidden",
													textOverflow: "ellipsis",
													whiteSpace: "nowrap",
												}}
											>
												{item.title}
											</span>
										</Link>
										<button
											type="button"
											onClick={(e) => handleDelete(e, item.id)}
											style={{
												position: "absolute",
												right: "8px",
												top: "50%",
												transform: "translateY(-50%)",
												background: "none",
												border: "none",
												color: "var(--ink-40)",
												cursor: "pointer",
												display: "flex",
												alignItems: "center",
												justifyContent: "center",
												padding: "4px",
												borderRadius: "3px",
												zIndex: 10,
											}}
											title="Xóa cuộc trò chuyện"
											onMouseEnter={(e) => {
												e.currentTarget.style.color = "var(--danger)";
											}}
											onMouseLeave={(e) => {
												e.currentTarget.style.color = "var(--ink-40)";
											}}
										>
											<TrashIcon />
										</button>
									</div>
								))}
							</div>
						))}
					</div>
				)}
			</div>

			{/* Footer */}
			<div className="sb-footer">
				<div className="sb-avatar">
					{userProfile?.name
						? userProfile.name.slice(0, 2).toUpperCase()
						: "KT"}
				</div>
				<div className="sb-who">
					<div className="sb-who-name">
						{userProfile?.name || "Kế toán viên"}
					</div>
					<div className="sb-who-role">
						{userProfile?.role || "Auditor"} ·{" "}
						{userProfile?.workspace || "Default"}
					</div>
				</div>
				<button
					type="button"
					className="sb-icon-btn"
					title="Toggle theme"
					onClick={onToggleTheme}
				>
					{theme === "dark" ? <SunIcon /> : <MoonIcon />}
				</button>
				<Link href="/settings" className="sb-icon-btn" title="Settings">
					<GearIcon />
				</Link>
				<button
					type="button"
					className="sb-icon-btn"
					title="Đăng xuất"
					onClick={handleSignOut}
				>
					<SignOutIcon />
				</button>
			</div>
		</aside>
	);
}
