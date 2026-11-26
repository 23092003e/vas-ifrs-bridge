"use client";

import {
	type DocumentItem,
	parseDocumentsResponse,
	validateDocumentFile,
} from "@/lib/documents/validation";
import { useCallback, useEffect, useRef, useState } from "react";

function getErrorMessage(error: unknown, fallback: string) {
	return error instanceof Error ? error.message : fallback;
}

async function getResponseError(response: Response, fallback: string) {
	try {
		const payload: unknown = await response.json();
		if (
			typeof payload === "object" &&
			payload !== null &&
			"detail" in payload &&
			typeof payload.detail === "string"
		) {
			return payload.detail;
		}
	} catch {
		// Use the stable fallback below.
	}
	return fallback;
}

export default function DocumentsPage() {
	const [docs, setDocs] = useState<DocumentItem[]>([]);
	const [loading, setLoading] = useState(true);
	const [uploading, setUploading] = useState(false);
	const [error, setError] = useState("");
	const fileInputRef = useRef<HTMLInputElement>(null);
	const hasActiveDocuments = docs.some(
		(document) =>
			document.status === "pending" || document.status === "processing",
	);

	const fetchDocuments = useCallback(async (signal?: AbortSignal) => {
		try {
			const response = await fetch("/api/documents", { signal });
			if (!response.ok) {
				throw new Error(
					await getResponseError(response, "Failed to load documents"),
				);
			}
			setDocs(parseDocumentsResponse(await response.json()));
			setError("");
		} catch (error) {
			if (signal?.aborted) return;
			console.error("Failed to load documents", error);
			setError(getErrorMessage(error, "Failed to load documents"));
		} finally {
			if (!signal?.aborted) setLoading(false);
		}
	}, []);

	// Fetch initial documents on mount
	useEffect(() => {
		const controller = new AbortController();
		void fetchDocuments(controller.signal);
		return () => controller.abort();
	}, [fetchDocuments]);

	// Poll documents if any is pending/processing
	useEffect(() => {
		if (!hasActiveDocuments) return;

		const interval = setInterval(() => void fetchDocuments(), 4000);

		return () => clearInterval(interval);
	}, [hasActiveDocuments, fetchDocuments]);

	const handleUploadClick = () => {
		fileInputRef.current?.click();
	};

	const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
		const files = e.target.files;
		if (!files || files.length === 0) return;

		const file = files[0];
		const validationError = validateDocumentFile(file);
		if (validationError) {
			setError(validationError);
			e.target.value = "";
			return;
		}
		setUploading(true);
		setError("");

		const formData = new FormData();
		formData.append("file", file);

		try {
			const response = await fetch("/api/documents", {
				method: "POST",
				body: formData,
			});

			if (!response.ok) {
				throw new Error(await getResponseError(response, "Upload failed"));
			}

			await fetchDocuments();
		} catch (error) {
			console.error("Failed to upload document", error);
			setError(getErrorMessage(error, "Upload failed"));
		} finally {
			if (fileInputRef.current) fileInputRef.current.value = "";
			setUploading(false);
		}
	};

	const statusColor = (s: string) => {
		if (s === "ready" || s === "Indexed") return "var(--score-high)";
		if (s === "processing" || s === "Processing") return "var(--score-mid)";
		if (s === "failed" || s === "Failed") return "var(--danger)";
		return "var(--ink-20)";
	};

	function formatBytes(bytes: number, decimals = 1) {
		if (bytes === 0) return "0 Bytes";
		const k = 1024;
		const dm = decimals < 0 ? 0 : decimals;
		const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return `${Number.parseFloat((bytes / k ** i).toFixed(dm))} ${sizes[i]}`;
	}

	function formatDate(isoString: string) {
		try {
			const d = new Date(isoString);
			return d.toLocaleDateString("vi-VN");
		} catch {
			return isoString;
		}
	}

	return (
		<div style={{ flex: 1, overflow: "auto", background: "var(--chat-bg)" }}>
			<div
				style={{
					padding: "24px 32px 16px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--surface)",
					display: "flex",
					alignItems: "flex-end",
					justifyContent: "space-between",
				}}
			>
				<div>
					<div
						style={{
							width: 32,
							height: 2,
							background: "var(--accent)",
							marginBottom: 12,
						}}
					/>
					<h1
						style={{
							margin: "0 0 4px",
							fontFamily: "var(--font-lora, Georgia, serif)",
							fontSize: "1.375rem",
							fontWeight: 700,
							color: "var(--ink)",
							letterSpacing: "-0.01em",
						}}
					>
						Cơ sở tri thức (KB)
					</h1>
					<p
						style={{
							margin: 0,
							fontSize: "0.82rem",
							fontStyle: "italic",
							fontFamily: "var(--font-lora, Georgia, serif)",
							color: "var(--ink-40)",
						}}
					>
						Tải lên tài liệu tham khảo (PDF, Word, Excel) dành riêng cho tổ chức
						của bạn
					</p>
				</div>
				<div>
					<input
						type="file"
						ref={fileInputRef}
						onChange={handleFileChange}
						style={{ display: "none" }}
						accept=".pdf,.docx,.xlsx,.txt,.md,.csv"
					/>
					<button
						type="button"
						onClick={handleUploadClick}
						disabled={uploading}
						style={{
							padding: "8px 16px",
							borderRadius: 3,
							background: uploading ? "var(--rule-strong)" : "var(--accent)",
							color: "#fff",
							border: "none",
							fontSize: "0.72rem",
							fontWeight: 700,
							fontFamily: "var(--font-mono)",
							letterSpacing: "0.05em",
							cursor: uploading ? "wait" : "pointer",
						}}
					>
						{uploading ? "ĐANG TẢI LÊN..." : "+ TẢI TÀI LIỆU LÊN"}
					</button>
				</div>
			</div>

			<div
				style={{
					padding: "16px 32px",
					borderBottom: "1px solid var(--rule)",
					background: "var(--paper-alt)",
					display: "flex",
					gap: 40,
				}}
			>
				{[
					["Tài liệu", docs.length.toString()],
					[
						"Số đoạn (Chunks)",
						docs
							.reduce((acc, d) => acc + (d.chunk_count || 0), 0)
							.toLocaleString(),
					],
					[
						"Hoàn tất",
						docs.filter((d) => d.status === "ready").length.toString(),
					],
					[
						"Tổng dung lượng",
						formatBytes(docs.reduce((acc, d) => acc + (d.size_bytes || 0), 0)),
					],
				].map(([l, v]) => (
					<div key={l}>
						<p
							style={{
								margin: "0 0 2px",
								fontSize: "0.6rem",
								fontFamily: "var(--font-mono)",
								color: "var(--ink-40)",
								letterSpacing: "0.06em",
								textTransform: "uppercase",
							}}
						>
							{l}
						</p>
						<p
							style={{
								margin: 0,
								fontSize: "1.125rem",
								fontWeight: 700,
								fontFamily: "var(--font-mono)",
								color: "var(--ink)",
							}}
						>
							{v}
						</p>
					</div>
				))}
			</div>

			<div style={{ padding: "24px 32px" }}>
				{error && (
					<div
						style={{
							padding: "12px 16px",
							background: "#fef2f2",
							color: "#991b1b",
							border: "1.5px solid #fca5a5",
							borderRadius: 3,
							fontSize: "0.8rem",
							fontFamily: "var(--font-mono)",
							marginBottom: 20,
						}}
					>
						{error}
					</div>
				)}

				{loading ? (
					<div
						style={{
							textAlign: "center",
							padding: "40px",
							fontFamily: "var(--font-mono)",
							fontSize: "0.8rem",
							color: "var(--ink-40)",
						}}
					>
						ĐANG TẢI TÀI LIỆU...
					</div>
				) : docs.length === 0 ? (
					<div
						style={{
							textAlign: "center",
							padding: "60px 40px",
							border: "1.5px dashed var(--rule-strong)",
							borderRadius: 4,
							background: "var(--surface)",
						}}
					>
						<p
							style={{
								margin: "0 0 12px",
								fontFamily: "var(--font-lora, Georgia, serif)",
								fontSize: "1rem",
								color: "var(--ink-60)",
								fontStyle: "italic",
							}}
						>
							Chưa có tài liệu nào trong thư viện của bạn.
						</p>
						<button
							type="button"
							onClick={handleUploadClick}
							style={{
								padding: "6px 12px",
								borderRadius: 3,
								background: "none",
								border: "1.5px solid var(--accent)",
								color: "var(--accent)",
								fontSize: "0.68rem",
								fontWeight: 700,
								fontFamily: "var(--font-mono)",
								cursor: "pointer",
							}}
						>
							TẢI LÊN FILE ĐẦU TIÊN
						</button>
					</div>
				) : (
					<table style={{ width: "100%", borderCollapse: "collapse" }}>
						<thead>
							<tr style={{ borderBottom: "2px solid var(--ink)" }}>
								{[
									"Tên tài liệu",
									"Kích thước",
									"Trạng thái",
									"Số Chunks",
									"Ngày thêm",
								].map((h) => (
									<th
										key={h}
										style={{
											padding: "8px 12px",
											textAlign: "left",
											fontSize: "0.6rem",
											fontFamily: "var(--font-mono)",
											fontWeight: 700,
											color: "var(--ink-60)",
											letterSpacing: "0.06em",
											textTransform: "uppercase",
										}}
									>
										{h}
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{docs.map((d, i) => {
								const ext = d.filename.split(".").pop() || "";
								return (
									<tr
										key={d.id || i}
										style={{
											borderBottom: "1px solid var(--rule)",
										}}
										onMouseEnter={(e) => {
											(e.currentTarget as HTMLElement).style.background =
												"var(--accent-light)";
										}}
										onMouseLeave={(e) => {
											(e.currentTarget as HTMLElement).style.background =
												"transparent";
										}}
									>
										<td style={{ padding: "11px 12px" }}>
											<div
												style={{
													display: "flex",
													alignItems: "center",
													gap: 8,
												}}
											>
												<span
													style={{
														fontSize: "0.58rem",
														fontFamily: "var(--font-mono)",
														fontWeight: 700,
														padding: "1px 5px",
														borderRadius: 2,
														background: ext === "pdf" ? "#fef2f2" : "#eff6ff",
														color: ext === "pdf" ? "#dc2626" : "#2563eb",
													}}
												>
													{ext.toUpperCase()}
												</span>
												<span
													style={{
														fontSize: "0.78rem",
														fontFamily: "var(--font-mono)",
														color: "var(--ink)",
													}}
												>
													{d.filename}
												</span>
											</div>
										</td>
										<td
											style={{
												padding: "11px 12px",
												fontSize: "0.73rem",
												fontFamily: "var(--font-mono)",
												color: "var(--ink-40)",
											}}
										>
											{formatBytes(d.size_bytes)}
										</td>
										<td style={{ padding: "11px 12px" }}>
											<span
												style={{
													fontSize: "0.65rem",
													fontFamily: "var(--font-mono)",
													fontWeight: 700,
													color: statusColor(d.status),
												}}
											>
												{d.status === "ready"
													? "Đã nạp"
													: d.status.toUpperCase()}
											</span>
										</td>
										<td
											style={{
												padding: "11px 12px",
												fontSize: "0.73rem",
												fontFamily: "var(--font-mono)",
												color: "var(--ink-40)",
											}}
										>
											{d.chunk_count > 0 ? d.chunk_count.toLocaleString() : "—"}
										</td>
										<td
											style={{
												padding: "11px 12px",
												fontSize: "0.7rem",
												fontFamily: "var(--font-mono)",
												color: "var(--ink-40)",
											}}
										>
											{formatDate(d.created_at)}
										</td>
									</tr>
								);
							})}
						</tbody>
					</table>
				)}
			</div>
		</div>
	);
}
