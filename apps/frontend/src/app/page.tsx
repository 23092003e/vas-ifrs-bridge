"use client";

import { FinancialTicker } from "@/components/landing/FinancialTicker";
import { LandingBackground } from "@/components/landing/LandingBackground";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

/* ── Standard Comparison Demo Data ── */
interface DemoTopic {
	id: string;
	title: string;
	vasStandard: string;
	ifrsStandard: string;
	headline: string;
	keyDifferences: {
		label: string;
		vas: string;
		ifrs: string;
		impact: string;
	}[];
	suggestedEntry: {
		dr: string;
		cr: string;
		amount: string;
		note: string;
	};
}

const DEMO_TOPICS: DemoTopic[] = [
	{
		id: "revenue",
		title: "Doanh thu & Hợp đồng",
		vasStandard: "VAS 14 (Doanh thu)",
		ifrsStandard: "IFRS 15 (Doanh thu HĐ)",
		headline: "Mô hình 5 bước ghi nhận doanh thu từ hợp đồng với khách hàng",
		keyDifferences: [
			{
				label: "Thời điểm ghi nhận",
				vas: "Khi chuyển giao phần lớn rủi ro & lợi ích gắn liền với quyền sở hữu.",
				ifrs: "Khi khách hàng nhận được quyền kiểm soát (Control) hàng hóa hoặc dịch vụ.",
				impact: "Chuyển từ cơ sở quyền sở hữu sang quyền kiểm soát thực tế.",
			},
			{
				label: "Hợp đồng đa nghĩa vụ",
				vas: "Thường ghi nhận gộp toàn bộ hợp đồng tại thời điểm bàn giao hàng.",
				ifrs: "Phải bóc tách riêng từng Nghĩa vụ thực hiện (PO) và phân bổ giá giao dịch.",
				impact: "Tách gói bán máy kèm dịch vụ bảo hành/bảo trì 2 năm.",
			},
			{
				label: "Chiết khấu & Thưởng DT",
				vas: "Hạch toán giảm trừ doanh thu khi khách hàng đạt sản lượng thực tế.",
				ifrs: "Ước tính Giá trị Biến đổi (Variable Consideration) ngay từ ban đầu.",
				impact: "Trích lập giảm trừ doanh thu tạm tính từng kỳ.",
			},
		],
		suggestedEntry: {
			dr: "Nợ: Doanh thu bán hàng (Hàng hóa) — 850,000,000 VND",
			cr: "Có: Doanh thu chưa thực hiện (Contract Liability) — 850,000,000 VND",
			amount: "850,000,000 VND",
			note: "IFRS 15 §73 — Tách phần giá trị phân bổ cho nghĩa vụ bảo trì 2 năm chưa thực hiện.",
		},
	},
	{
		id: "leases",
		title: "Thuê tài sản",
		vasStandard: "VAS 06 (Thuê tài sản)",
		ifrsStandard: "IFRS 16 (Thuê tài sản)",
		headline: "Vốn hóa quyền sử dụng tài sản (ROU Asset) và Nợ thuê tài chính",
		keyDifferences: [
			{
				label: "Ghi nhận Bảng CĐKT",
				vas: "Thuê hoạt động ghi nhận chi phí vào P&L theo kỳ, ngoài bảng CĐKT.",
				ifrs: "Gần như toàn bộ hợp đồng thuê trên 12 tháng đều phải ghi nhận vào Bảng CĐKT.",
				impact:
					"Ghi nhận Tài sản Quyền sử dụng (ROU) và Nợ phải trả thuê tài sản.",
			},
			{
				label: "Tác động P&L",
				vas: "Chi phí thuê hoạt động tính đều theo đường thẳng vào chi phí quản lý.",
				ifrs: "Chi phí chia thành 2 phần: Khấu hao ROU Asset + Chi phí lãi vay (Interest).",
				impact:
					"EBITDA tăng đáng kể do chi phí thuê chuyển xuống dưới dòng EBIT.",
			},
			{
				label: "Tỷ lệ đòn bẩy",
				vas: "Không làm tăng hệ số nợ/vốn chủ sở hữu (Debt/Equity) của doanh nghiệp.",
				ifrs: "Nợ phải trả tài chính tăng cao, có thể vi phạm các giao ước vay (Debt Covenants).",
				impact:
					"Cần tái thương thảo hạn mức tín dụng với các ngân hàng tài trợ.",
			},
		],
		suggestedEntry: {
			dr: "Nợ: Right-of-Use Asset (Tài sản ROU) — 14,200,000,000 VND",
			cr: "Có: Lease Liability (Nợ thuê tài chính) — 14,200,000,000 VND",
			amount: "14,200,000,000 VND",
			note: "IFRS 16 §22 — Hiện giá dòng tiền thuê văn phòng 5 năm theo lãi suất biên vay 7.5%.",
		},
	},
	{
		id: "instruments",
		title: "Công cụ tài chính & Dự phòng",
		vasStandard: "Thông tư 48 / VAS 22",
		ifrsStandard: "IFRS 9 (Công cụ tài chính)",
		headline: "Mô hình tổn thất tín dụng dự kiến (Expected Credit Loss - ECL)",
		keyDifferences: [
			{
				label: "Cơ chế trích lập",
				vas: "Mô hình tổn thất đã phát sinh (Incurred Loss) dựa trên số ngày quá hạn.",
				ifrs: "Mô hình tổn thất dự kiến (ECL) 3 giai đoạn kết hợp số liệu vĩ mô quá khứ & tương lai.",
				impact: "Trích lập dự phòng ngay khi giải ngân/phát sinh nợ (Stage 1).",
			},
			{
				label: "Phân loại tài sản TC",
				vas: "Phân loại theo mục đích dự định nắm giữ ban đầu (Kinh doanh, Đầu tư).",
				ifrs: "Đánh giá theo Mô hình kinh doanh (Business Model) và Đặc điểm dòng tiền (SPPI).",
				impact:
					"Đo lường theo Giá trị hợp lý thông qua P&L hoặc OCI (FVTPL / FVOCI).",
			},
			{
				label: "Tài sản phái sinh",
				vas: "Ghi nhận ngoại bảng hoặc chỉ ghi nhận chênh lệch tỷ giá cuối kỳ.",
				ifrs: "Bắt buộc ghi nhận nội bảng theo Giá trị hợp lý (Fair Value) tại mọi kỳ báo cáo.",
				impact:
					"Biến động mạnh lợi nhuận thuần đối với hợp đồng Forward, Swap, Option.",
			},
		],
		suggestedEntry: {
			dr: "Nợ: ECL Impairment Loss (Chi phí dự phòng P&L) — 620,000,000 VND",
			cr: "Có: Allowance for Expected Credit Loss — 620,000,000 VND",
			amount: "620,000,000 VND",
			note: "IFRS 9 §5.5 — Trích lập ECL Stage 1 cho danh mục nợ phải thu thương mại ngắn hạn.",
		},
	},
];

/* ── Workflow Pipeline Data ── */
const PIPELINE_STEPS = [
	{
		step: "01",
		title: "Nạp Bảng CĐPS (Trial Balance)",
		desc: "Nhập khẩu tệp Excel/CSV Bảng cân đối phát sinh tài khoản theo Thông tư 200/2014/TT-BTC. Hệ thống tự động kiểm tra số dư và cấu trúc dữ liệu.",
		tag: "Ingestion Engine",
	},
	{
		step: "02",
		title: "AI Semantic Account Mapping",
		desc: "Mô hình Knowledge Graph tự động phân tích và ghép nối tài khoản VAS (111-911) sang danh mục Báo cáo IFRS tương đương với chỉ số tin cậy minh bạch.",
		tag: "Knowledge Graph",
	},
	{
		step: "03",
		title: "Đề xuất Bút toán Điều chỉnh",
		desc: "Tự động sinh các bút toán tái phân loại (Reclassification) và tái đo lường (Remeasurement) theo IFRS 16, IFRS 15, IFRS 9, IAS 12 kèm nhật ký giải trình.",
		tag: "Audit Trail",
	},
	{
		step: "04",
		title: "Xuất Báo cáo & Thuyết minh",
		desc: "Tạo Báo cáo Tình hình Tài chính, Báo cáo Kết quả Hoạt động và Bộ Thuyết minh IFRS song ngữ (VI/EN) sẵn sàng gửi cho kiểm toán viên độc lập.",
		tag: "IFRS Financials",
	},
];

export default function LandingPage() {
	const [activeDemoId, setActiveDemoId] = useState<string>("revenue");
	const [activePipelineIndex, setActivePipelineIndex] = useState<number>(0);
	const [activeSection, setActiveSection] = useState<string>("");

	// Dedicated Smooth Scroll Engine with easeInOutCubic & distance-based duration
	const smoothScrollTo = useCallback(
		(targetIdOrY: string | number, customDuration?: number) => {
			let targetY = 0;
			if (typeof targetIdOrY === "string") {
				if (targetIdOrY === "top") {
					targetY = 0;
				} else {
					const el = document.getElementById(targetIdOrY);
					if (!el) return;
					const navOffset = 84;
					targetY = Math.max(
						0,
						el.getBoundingClientRect().top + window.scrollY - navOffset,
					);
				}
			} else {
				targetY = Math.max(0, targetIdOrY);
			}

			const startY = window.scrollY;
			const distance = Math.abs(targetY - startY);
			if (distance < 2) return;

			// Adaptive luxurious glide duration (650ms - 850ms)
			const duration =
				customDuration ??
				Math.min(850, Math.max(650, Math.round(Math.sqrt(distance) * 18)));
			const startTime = performance.now();

			// Clean up any existing running animation
			const winObj = window as unknown as { __vasScrollAnim?: number };
			if (winObj.__vasScrollAnim) {
				cancelAnimationFrame(winObj.__vasScrollAnim);
			}

			// Ensure instant frame-by-frame control during RAF
			document.documentElement.style.scrollBehavior = "auto";

			let isCancelled = false;
			const cleanup = () => {
				window.removeEventListener("wheel", cancel);
				window.removeEventListener("touchmove", cancel);
				document.documentElement.style.scrollBehavior = "";
				winObj.__vasScrollAnim = undefined;
			};

			const cancel = () => {
				isCancelled = true;
				cleanup();
			};
			window.addEventListener("wheel", cancel, { passive: true });
			window.addEventListener("touchmove", cancel, { passive: true });

			const step = (currentTime: number) => {
				if (isCancelled) return;
				const elapsed = currentTime - startTime;
				const progress = Math.min(elapsed / duration, 1);

				// Luxurious easeInOutCubic curve
				const ease =
					progress < 0.5
						? 4 * progress * progress * progress
						: 1 - (-2 * progress + 2) ** 3 / 2;

				window.scrollTo(0, startY + (targetY - startY) * ease);

				if (progress < 1) {
					winObj.__vasScrollAnim = requestAnimationFrame(step);
				} else {
					cleanup();
				}
			};

			winObj.__vasScrollAnim = requestAnimationFrame(step);

			if (typeof targetIdOrY === "string" && targetIdOrY !== "top") {
				window.history.pushState(null, "", `#${targetIdOrY}`);
			}
		},
		[],
	);

	// Global anchor click interceptor for all internal anchor hash links
	useEffect(() => {
		const handleAnchorClick = (e: MouseEvent) => {
			const link = (e.target as HTMLElement).closest('a[href^="#"]');
			if (!link) return;
			const href = link.getAttribute("href");
			if (!href || href === "#") return;
			const targetId = href.substring(1);
			const el = document.getElementById(targetId);
			if (el) {
				e.preventDefault();
				smoothScrollTo(targetId);
			}
		};

		document.addEventListener("click", handleAnchorClick);
		return () => document.removeEventListener("click", handleAnchorClick);
	}, [smoothScrollTo]);

	// Active Section Spy for Floating Dock
	useEffect(() => {
		const sections = ["matrix", "standards", "pillars", "pipeline"];
		const handleScroll = () => {
			const scrollPos = window.scrollY + 160;
			let current = "";
			for (const id of sections) {
				const el = document.getElementById(id);
				if (el) {
					const top = el.offsetTop;
					const height = el.offsetHeight;
					if (scrollPos >= top && scrollPos < top + height) {
						current = id;
						break;
					}
				}
			}
			setActiveSection(current);
		};

		window.addEventListener("scroll", handleScroll, { passive: true });
		handleScroll();
		return () => window.removeEventListener("scroll", handleScroll);
	}, []);

	// Scroll-Triggered Reveal Animations
	useEffect(() => {
		if (typeof IntersectionObserver === "undefined") return;
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) {
						entry.target.classList.add("is-revealed");
					}
				}
			},
			{ threshold: 0.08, rootMargin: "0px 0px -40px 0px" },
		);

		const elements = document.querySelectorAll(".reveal-on-scroll");
		for (const el of Array.from(elements)) {
			observer.observe(el);
		}

		return () => observer.disconnect();
	}, []);

	// Bento card mouse spotlight tracking
	const handleCardMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
		const rect = e.currentTarget.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;
		e.currentTarget.style.setProperty("--card-x", `${x}px`);
		e.currentTarget.style.setProperty("--card-y", `${y}px`);
	};

	const currentDemo =
		DEMO_TOPICS.find((t) => t.id === activeDemoId) || DEMO_TOPICS[0];

	return (
		<div className="landing-root">
			{/* Dynamic Interactive Background */}
			<LandingBackground />

			{/* ── 1. Header & Floating Dock Navigation ── */}
			<header className="landing-nav-wrap">
				<nav className="landing-dock" aria-label="Điều hướng chính">
					{/* Brand Monogram & Name - Smooth Scroll to Top */}
					<button
						type="button"
						onClick={() => smoothScrollTo("top")}
						className="landing-brand landing-brand-btn"
						aria-label="Cuộn về đầu trang"
					>
						<div className="landing-brand-mark">V</div>
						<div className="landing-brand-text">
							<span className="landing-brand-name">VAS·IFRS</span>
							<span className="landing-brand-sub">Bridge</span>
						</div>
					</button>

					{/* Center Dock Links with Smooth Scroll & Active Indicator */}
					<div className="landing-dock-links">
						<a
							href="#matrix"
							onClick={(e) => {
								e.preventDefault();
								smoothScrollTo("matrix");
							}}
							className={`landing-dock-item ${activeSection === "matrix" ? "active" : ""}`}
							data-active={activeSection === "matrix" ? "true" : undefined}
						>
							Ma trận So sánh
						</a>
						<a
							href="#pipeline"
							onClick={(e) => {
								e.preventDefault();
								smoothScrollTo("pipeline");
							}}
							className={`landing-dock-item ${activeSection === "pipeline" ? "active" : ""}`}
							data-active={activeSection === "pipeline" ? "true" : undefined}
						>
							Quy trình GL
						</a>
						<a
							href="#pillars"
							onClick={(e) => {
								e.preventDefault();
								smoothScrollTo("pillars");
							}}
							className={`landing-dock-item ${activeSection === "pillars" ? "active" : ""}`}
							data-active={activeSection === "pillars" ? "true" : undefined}
						>
							Trụ cột Nền tảng
						</a>
						<a
							href="#standards"
							onClick={(e) => {
								e.preventDefault();
								smoothScrollTo("standards");
							}}
							className={`landing-dock-item ${activeSection === "standards" ? "active" : ""}`}
							data-active={activeSection === "standards" ? "true" : undefined}
						>
							Chuẩn mực
						</a>
					</div>

					{/* Actions */}
					<div className="landing-dock-actions">
						<Link href="/login" className="landing-btn-secondary">
							Đăng nhập
						</Link>
						<Link href="/chat" className="landing-btn-primary">
							<span>Trải nghiệm ngay</span>
							<span className="btn-arrow">→</span>
						</Link>
					</div>
				</nav>
			</header>

			{/* Live Financial Standards Ticker Ribbon */}
			<FinancialTicker />

			<main>
				{/* ── 2. Hero Section (High-Impact & Interactive) ── */}
				<section className="landing-hero-section">
					<div className="landing-hero-content reveal-on-scroll is-revealed">
						{/* Eyebrow badge */}
						<div className="landing-eyebrow">
							<span className="landing-pulse-dot" />
							<span>HỆ THỐNG ĐỐI CHIẾU CHUẨN MỰC KẾ TOÁN VAS ↔ IFRS</span>
						</div>

						{/* Headline (Max 2 lines desktop) */}
						<h1 className="landing-hero-title">
							Thu hẹp khoảng cách giữa VAS và IFRS
							<br />
							<span className="landing-title-italic">
								với độ chính xác chuẩn kiểm toán.
							</span>
						</h1>

						{/* Subheadline (Max 20 words) */}
						<p className="landing-hero-sub">
							Ứng dụng RAG và Knowledge Graph tự động phát hiện khác biệt ghi
							nhận, đề xuất bút toán điều chỉnh và lập thuyết minh tài chính
							minh bạch.
						</p>

						{/* Dual CTAs */}
						<div className="landing-hero-ctas">
							<Link href="/chat" className="landing-cta-primary">
								<span>Bắt đầu thử nghiệm</span>
								<span className="btn-arrow">→</span>
							</Link>
							<a
								href="#matrix"
								onClick={(e) => {
									e.preventDefault();
									smoothScrollTo("matrix");
								}}
								className="landing-cta-secondary"
							>
								<span>Khám phá Ma trận Chuẩn mực</span>
								<span className="btn-arrow">↓</span>
							</a>
						</div>
					</div>

					{/* ── Live Interactive Demo Widget (Hero Preview) ── */}
					<div
						className="landing-demo-container reveal-on-scroll is-revealed"
						id="matrix"
					>
						<div className="landing-demo-window">
							{/* Window Header */}
							<div className="landing-demo-header">
								<div className="landing-window-dots">
									<span className="window-dot dot-red" />
									<span className="window-dot dot-yellow" />
									<span className="window-dot dot-green" />
								</div>
								<div className="landing-demo-title">
									VAS-IFRS RECONCILIATION TERMINAL — LIVE DIFFERENCE ENGINE
								</div>
								<div className="landing-demo-meta">
									<span className="demo-chip-live">ENGINE: ACTIVE</span>
								</div>
							</div>

							{/* Standard Tabs */}
							<div className="landing-demo-tabs">
								{DEMO_TOPICS.map((topic) => (
									<button
										key={topic.id}
										type="button"
										onClick={() => setActiveDemoId(topic.id)}
										className="landing-demo-tab"
										data-active={activeDemoId === topic.id ? "true" : undefined}
									>
										<span className="demo-tab-vas">{topic.vasStandard}</span>
										<span className="demo-tab-arr">➔</span>
										<span className="demo-tab-ifrs">{topic.ifrsStandard}</span>
									</button>
								))}
							</div>

							{/* Comparison Split View with smooth transition */}
							<div
								key={activeDemoId}
								className="landing-demo-body landing-demo-animated"
							>
								<div className="landing-demo-headline">
									<div className="demo-headline-label">NỘI DUNG ĐỐI CHIẾU:</div>
									<div className="demo-headline-text">
										{currentDemo.headline}
									</div>
								</div>

								<div className="landing-diff-grid">
									{currentDemo.keyDifferences.map((diff) => (
										<div key={diff.label} className="landing-diff-card">
											<div className="diff-card-header">
												<span className="diff-label">{diff.label}</span>
												<span className="diff-impact-badge">{diff.impact}</span>
											</div>
											<div className="diff-card-columns">
												<div className="diff-col diff-col-vas">
													<div className="diff-col-tag">VAS (VN)</div>
													<div className="diff-col-text">{diff.vas}</div>
												</div>
												<div className="diff-col diff-col-ifrs">
													<div className="diff-col-tag">IFRS (QT)</div>
													<div className="diff-col-text">{diff.ifrs}</div>
												</div>
											</div>
										</div>
									))}
								</div>

								{/* Suggested Journal Entry Box */}
								<div className="landing-entry-box">
									<div className="entry-box-header">
										<span className="entry-box-title">
											BÚT TOÁN ĐIỀU CHỈNH CHUYỂN ĐỔI GỢI Ý (ADJUSTING JOURNAL
											ENTRY)
										</span>
										<span className="entry-standard-badge">
											{currentDemo.suggestedEntry.note}
										</span>
									</div>
									<div className="entry-code-block">
										<div className="entry-line entry-dr">
											{currentDemo.suggestedEntry.dr}
										</div>
										<div className="entry-line entry-cr">
											{currentDemo.suggestedEntry.cr}
										</div>
									</div>
								</div>
							</div>

							{/* Widget Action Strip */}
							<div className="landing-demo-footer">
								<div className="demo-footer-info">
									Trích lục trực tiếp từ cơ sở dữ liệu Thông tư 200/2014/TT-BTC
									& IFRS Bound Volume.
								</div>
								<Link
									href={`/compare?vas=${currentDemo.vasStandard.split(" ")[0]}&ifrs=${currentDemo.ifrsStandard.split(" ")[0]}`}
									className="demo-footer-btn"
								>
									<span>Xem đầy đủ trong Compare Matrix</span>
									<span className="btn-arrow">→</span>
								</Link>
							</div>
						</div>
					</div>
				</section>

				{/* ── 3. Trust & Compliance Bar ── */}
				<section className="landing-trust-bar reveal-on-scroll" id="standards">
					<div className="landing-trust-inner">
						<div className="trust-heading">
							CƠ SỞ PHÁP LÝ & QUY CHUẨN KẾ TOÁN ÁP DỤNG
						</div>
						<div className="trust-badges">
							<div className="trust-badge">
								<span className="trust-dot" />
								<span className="trust-code">IFRS 15</span>
								<span className="trust-label">Doanh thu Hợp đồng</span>
							</div>
							<div className="trust-badge">
								<span className="trust-dot" />
								<span className="trust-code">IFRS 16</span>
								<span className="trust-label">Thuê tài sản & ROU</span>
							</div>
							<div className="trust-badge">
								<span className="trust-dot" />
								<span className="trust-code">IFRS 9</span>
								<span className="trust-label">Tổn thất tín dụng ECL</span>
							</div>
							<div className="trust-badge">
								<span className="trust-dot" />
								<span className="trust-code">IAS 12</span>
								<span className="trust-label">Thuế TNDN hoãn lại</span>
							</div>
							<div className="trust-badge">
								<span className="trust-dot" />
								<span className="trust-code">TT 200/BTC</span>
								<span className="trust-label">Chế độ Kế toán Doanh nghiệp</span>
							</div>
							<div className="trust-badge">
								<span className="trust-dot" />
								<span className="trust-code">QĐ 345/QĐ-BTC</span>
								<span className="trust-label">Đề án Áp dụng IFRS tại VN</span>
							</div>
						</div>
					</div>
				</section>

				{/* ── 4. Bento Grid: Sức mạnh Cốt lõi của Nền tảng (The Core Pillars) ── */}
				<section className="landing-pillars-section" id="pillars">
					<div className="landing-section-header reveal-on-scroll">
						<h2 className="landing-section-title">
							Kiến trúc Chuyển đổi Báo cáo Tài chính
							<br />
							<span className="landing-title-italic">
								Dành riêng cho Kiểm toán viên & CFO.
							</span>
						</h2>
						<p className="landing-section-sub">
							Không còn phỏng đoán hay phụ thuộc vào các file bảng tính thủ công
							dễ sai sót. Mọi chuyển đổi đều có thể thẩm định và kiểm tra chéo.
						</p>
					</div>

					<div className="landing-bento-grid">
						{/* Card 1: Grounded RAG */}
						<div
							className="bento-cell bento-cell-large reveal-on-scroll"
							style={{ "--stagger-idx": 0 } as React.CSSProperties}
							onMouseMove={handleCardMouseMove}
						>
							<div className="bento-badge">PILLAR 01</div>
							<h3 className="bento-title">
								AI Trợ lý Chuẩn mực có Dẫn chứng (Grounded RAG)
							</h3>
							<p className="bento-desc">
								Mọi kết quả truy vấn, giải trình và khác biệt hạch toán đều được
								neo chặt chẽ vào các đoạn, số điều khoản chính xác của VAS 01–30
								và IFRS 1–17. Loại bỏ hoàn toàn ảo giác (hallucination).
							</p>
							<div className="bento-visual bento-rag-preview">
								<div className="rag-preview-card">
									<div className="rag-quote">
										"Theo IFRS 16 đoạn 22, tại ngày bắt đầu hợp đồng thuê, bên
										thuê phải ghi nhận tài sản quyền sử dụng và nợ phải trả thuê
										tài sản..."
									</div>
									<div className="rag-citation">
										<span className="citation-tag">Trích dẫn: IFRS 16 §22</span>
										<span className="citation-verified">
											✓ Đã xác thực chéo
										</span>
									</div>
								</div>
							</div>
						</div>

						{/* Card 2: Semantic Mapping Matrix */}
						<div
							className="bento-cell bento-cell-regular reveal-on-scroll"
							style={{ "--stagger-idx": 1 } as React.CSSProperties}
							onMouseMove={handleCardMouseMove}
						>
							<div className="bento-badge">PILLAR 02</div>
							<h3 className="bento-title">Semantic Account Mapping</h3>
							<p className="bento-desc">
								Bản đồ quan hệ tự động kết nối tài khoản VAS sang IFRS tương
								đương, tự động xử lý tài khoản lưỡng tính và chi tiết hóa số dư.
							</p>
							<div className="bento-visual bento-mapping-preview">
								<div className="mapping-row">
									<span className="map-vas">TK 131</span>
									<span className="map-arrow">➔</span>
									<span className="map-ifrs">Trade Receivables</span>
									<span className="map-score">99%</span>
								</div>
								<div className="mapping-row">
									<span className="map-vas">TK 341</span>
									<span className="map-arrow">➔</span>
									<span className="map-ifrs">Lease Liability</span>
									<span className="map-score">92%</span>
								</div>
							</div>
						</div>

						{/* Card 3: Audit-Trail First */}
						<div
							className="bento-cell bento-cell-regular reveal-on-scroll"
							style={{ "--stagger-idx": 2 } as React.CSSProperties}
							onMouseMove={handleCardMouseMove}
						>
							<div className="bento-badge">PILLAR 03</div>
							<h3 className="bento-title">Reconciliation Audit Trail</h3>
							<p className="bento-desc">
								Mọi bút toán điều chỉnh đều có nhật ký giải trình số liệu nguồn,
								công thức chiết khấu và dấu thời gian sẵn sàng cho Big 4 thẩm
								tra.
							</p>
							<div className="bento-visual bento-audit-preview">
								<div className="audit-log-entry">
									<span className="audit-status">AUDITED</span>
									<span className="audit-ref">#ADJ-ROU-2026-Q1</span>
									<span className="audit-hash">SHA-256 Verified</span>
								</div>
								<div className="audit-log-text">
									Duyệt bởi Lead Auditor · Không có chênh lệch chưa giải trình
								</div>
							</div>
						</div>

						{/* Card 4: Enterprise Multi-Tenant & Security */}
						<div
							className="bento-cell bento-cell-large reveal-on-scroll"
							style={{ "--stagger-idx": 3 } as React.CSSProperties}
							onMouseMove={handleCardMouseMove}
						>
							<div className="bento-badge">PILLAR 04</div>
							<h3 className="bento-title">
								Enterprise Multi-Tenant & Zero Data Training
							</h3>
							<p className="bento-desc">
								Bảo mật tuyệt đối dữ liệu tài chính nội bộ. Cơ sở dữ liệu vector
								được cách ly nghiêm ngặt theo Tenant ID. Cam kết không lưu giữ
								và không huấn luyện mô hình ngôn ngữ trên báo cáo tài chính của
								khách hàng.
							</p>
							<div className="bento-visual bento-sec-preview">
								<div className="sec-tag-group">
									<span className="sec-tag">Tenant Vector Isolation</span>
									<span className="sec-tag">SOC 2 Type II Ready</span>
									<span className="sec-tag">TLS 1.3 / AES-256</span>
									<span className="sec-tag">RBAC Role Enforcement</span>
								</div>
							</div>
						</div>
					</div>
				</section>

				{/* ── 5. Interactive Workflow Pipeline ("Từ Trial Balance VAS đến Báo cáo IFRS") ── */}
				<section className="landing-pipeline-section" id="pipeline">
					<div className="landing-section-header reveal-on-scroll">
						<h2 className="landing-section-title">
							Quy trình Chuyển đổi 4 Bước
							<br />
							<span className="landing-title-italic">
								Từ Bảng CĐPS VAS đến Báo cáo IFRS Hoàn chỉnh.
							</span>
						</h2>
						<p className="landing-section-sub">
							Khám phá luồng dữ liệu tự động giúp giảm 80% thời gian lập báo cáo
							chuyển đổi định kỳ của doanh nghiệp.
						</p>
					</div>

					<div className="landing-pipeline-stepper reveal-on-scroll">
						<div className="pipeline-nav">
							{PIPELINE_STEPS.map((item, index) => (
								<button
									key={item.step}
									type="button"
									onClick={() => setActivePipelineIndex(index)}
									className="pipeline-step-btn"
									data-active={
										activePipelineIndex === index ? "true" : undefined
									}
								>
									<div className="pipeline-step-num">{item.step}</div>
									<div className="pipeline-step-title">{item.title}</div>
								</button>
							))}
						</div>

						{/* Step Detail Card with smooth animated transition */}
						<div
							key={activePipelineIndex}
							className="pipeline-detail-card pipeline-card-animated"
						>
							<div className="pipeline-card-badge">
								{PIPELINE_STEPS[activePipelineIndex].tag}
							</div>
							<h3 className="pipeline-card-title">
								{PIPELINE_STEPS[activePipelineIndex].title}
							</h3>
							<p className="pipeline-card-desc">
								{PIPELINE_STEPS[activePipelineIndex].desc}
							</p>

							<div className="pipeline-card-action">
								<Link href="/gl/upload" className="pipeline-link-btn">
									<span>Mở Sandbox Trải nghiệm Quy trình</span>
									<span className="btn-arrow">→</span>
								</Link>
							</div>
						</div>
					</div>
				</section>

				{/* ── 6. Executive Conversion CTA & Financial Footer ── */}
				<section className="landing-cta-banner reveal-on-scroll">
					<div className="landing-cta-inner">
						<div className="cta-badge">LỘ TRÌNH IFRS TẠI VIỆT NAM</div>
						<h2 className="cta-title">
							Sẵn sàng chuẩn hóa hệ thống báo cáo tài chính cho lộ trình IFRS?
						</h2>
						<p className="cta-sub">
							Dành cho Ban Giám đốc, Kế toán trưởng và Chuyên viên Kiểm toán cần
							công cụ tham chiếu chuẩn mực chính xác, có căn cứ và có thể bảo vệ
							trước cơ quan thanh tra và kiểm toán độc lập.
						</p>
						<div className="cta-actions">
							<Link href="/chat" className="landing-cta-primary">
								<span>Bắt đầu Trải nghiệm ngay</span>
								<span className="btn-arrow">→</span>
							</Link>
							<Link href="/gl/upload" className="landing-cta-secondary">
								<span>Tải Template Sổ cái (.csv)</span>
								<span className="btn-arrow">↓</span>
							</Link>
						</div>
					</div>
				</section>
			</main>

			{/* Financial Terminal Footer */}
			<footer className="landing-footer">
				<div className="landing-footer-grid">
					<div className="footer-col-brand">
						<div className="landing-brand" style={{ marginBottom: 12 }}>
							<div className="landing-brand-mark">V</div>
							<div className="landing-brand-text">
								<span className="landing-brand-name">VAS·IFRS</span>
								<span className="landing-brand-sub">Bridge</span>
							</div>
						</div>
						<p className="footer-bio">
							Nền tảng trí tuệ nhân tạo chuyên biệt cho chuyển đổi và đối chiếu
							Báo cáo Tài chính theo Chuẩn mực Kế toán Quốc tế (IFRS) từ Chuẩn
							mực Việt Nam (VAS).
						</p>
						<div className="footer-compliance-tag">
							ISO/IEC 27001 Standard Aligned · Zero Data Retention
						</div>
					</div>

					<div className="footer-col">
						<div className="footer-col-title">CÔNG CỤ NỀN TẢNG</div>
						<ul className="footer-links">
							<li>
								<Link href="/chat">Nova Chat Assistant</Link>
							</li>
							<li>
								<Link href="/compare">Standards Diff Matrix</Link>
							</li>
							<li>
								<Link href="/gl/upload">GL Trial Balance Pipeline</Link>
							</li>
							<li>
								<Link href="/gl/mappings">Semantic Account Mapping</Link>
							</li>
							<li>
								<Link href="/gl/adjustments">IFRS Adjusting Entries</Link>
							</li>
							<li>
								<Link href="/reports">Financial Statement Export</Link>
							</li>
						</ul>
					</div>

					<div className="footer-col">
						<div className="footer-col-title">CHUẨN MỰC HỖ TRỢ</div>
						<ul className="footer-links">
							<li>IFRS 15 — Doanh thu hợp đồng</li>
							<li>IFRS 16 — Thuê tài sản & ROU</li>
							<li>IFRS 9 — Công cụ tài chính (ECL)</li>
							<li>IAS 12 — Thuế thu nhập doanh nghiệp</li>
							<li>Thông tư 200/2014/TT-BTC</li>
							<li>Quyết định 345/QĐ-BTC (Lộ trình IFRS)</li>
						</ul>
					</div>

					<div className="footer-col">
						<div className="footer-col-title">BẢO MẬT & PHÁP LÝ</div>
						<ul className="footer-links">
							<li>Multi-Tenant Isolation</li>
							<li>Chính sách Bảo mật Dữ liệu</li>
							<li>Nhật ký Kiểm toán (Audit Trail)</li>
							<li>Bảo vệ Dữ liệu Doanh nghiệp FDI</li>
						</ul>
					</div>
				</div>

				{/* Financial Times / Terminal Disclaimer */}
				<div className="footer-disclaimer-wrap">
					<p className="footer-disclaimer">
						<strong>Miễn trừ trách nhiệm nghiệp vụ kế toán:</strong> VAS-IFRS
						Bridge là hệ thống trợ lý công nghệ hỗ trợ tra cứu, đối chiếu và lập
						mô hình toán chuyển đổi dữ liệu. Nền tảng không đóng vai trò tổ chức
						hành nghề kiểm toán độc lập theo Luật Kiểm toán Độc lập số
						67/2011/QH12. Số liệu và đề xuất bút toán cần được soát xét bởi Kế
						toán trưởng hoặc Kiểm toán viên phụ trách trước khi công bố Báo cáo
						Tài chính chính thức.
					</p>
					<div className="footer-bottom-row">
						<div>© 2026 VAS-IFRS Bridge Engine. All rights reserved.</div>
						<div className="footer-mono-status">
							TERMINAL BUILD v2.6.4 · OKLCH
						</div>
					</div>
				</div>
			</footer>
		</div>
	);
}
