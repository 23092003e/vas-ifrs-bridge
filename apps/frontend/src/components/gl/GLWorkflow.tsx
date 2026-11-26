"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { downloadTrialBalanceTemplate } from "./trialBalanceTemplate";

type Step = "upload" | "mappings" | "adjustments" | "reports";
type Upload = { id: string; filename: string };
type Mapping = {
	src_account_code: string;
	src_account_name: string;
	target_account_code: string | null;
	source: string;
};
type TrialBalance = Upload & {
	row_count: number;
	mapped_count: number;
	mappings: Mapping[] | null;
};
type Line = { account: string; type: "debit" | "credit"; amount: string };
type Entry = {
	id: string;
	upload_id: string;
	source_account: string;
	note: string;
	status: string;
	lines: Line[] | null;
};
type Report = { id: string; upload_id: string; period: string };
type ReportDetails = Report & {
	source_total: string;
	approved_entry_ids: string[];
	rows: {
		account: string;
		mapped_balance: string;
		adjustment: string;
		adjusted_balance: string;
	}[];
};

const base = "/api/gl-workflow";
const field = "block rounded border border-border bg-background px-3 py-2";
const button =
	"rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50";
const titles: Record<Step, string> = {
	upload: "Tải bảng cân đối phát sinh",
	mappings: "Ánh xạ tài khoản",
	adjustments: "Bút toán điều chỉnh",
	reports: "Bảng cân đối phát sinh sau điều chỉnh",
};
const paths: Record<Step, string> = {
	upload: "/gl/upload",
	mappings: "/gl/mappings",
	adjustments: "/gl/adjustments",
	reports: "/reports",
};
const emptyLines = (): Line[] => [
	{ account: "", type: "debit", amount: "" },
	{ account: "", type: "credit", amount: "" },
];

async function api<T>(path: string, options?: RequestInit): Promise<T> {
	const response = await fetch(`${base}/${path}`, options);
	const data = await response.json();
	if (!response.ok) {
		throw new Error(
			typeof data.detail === "string"
				? data.detail
				: (data.detail?.[0]?.msg ?? "Yêu cầu không thành công"),
		);
	}
	return data as T;
}

function json(method: string, body: unknown): RequestInit {
	return {
		method,
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	};
}

export function GLWorkflow({ step }: { step: Step }) {
	const [uploads, setUploads] = useState<Upload[]>([]);
	const [selected, setSelected] = useState("");
	const [balance, setBalance] = useState<TrialBalance | null>(null);
	const [entries, setEntries] = useState<Entry[]>([]);
	const [reports, setReports] = useState<Report[]>([]);
	const [report, setReport] = useState<ReportDetails | null>(null);
	const [file, setFile] = useState<File>();
	const [source, setSource] = useState("");
	const [target, setTarget] = useState("");
	const [note, setNote] = useState("");
	const [period, setPeriod] = useState("");
	const [lines, setLines] = useState<Line[]>(emptyLines);
	const [error, setError] = useState("");
	const [message, setMessage] = useState("");
	const [busy, setBusy] = useState(false);
	const [loading, setLoading] = useState(false);
	const uploadKey = useRef("");
	const operationKey = useRef<{ payload: string; id: string } | null>(null);

	function keyFor(body: object) {
		const payload = JSON.stringify(body);
		if (operationKey.current?.payload !== payload)
			operationKey.current = { payload, id: crypto.randomUUID() };
		return operationKey.current.id;
	}

	const loadUploads = useCallback(async (signal?: AbortSignal) => {
		const items = await api<Upload[]>("gl", { signal });
		if (signal?.aborted) return;
		setUploads(items);
		const fromLink = new URLSearchParams(window.location.search).get("upload");
		setSelected(
			(current) =>
				current ||
				items.find((item) => item.id === fromLink)?.id ||
				items[0]?.id ||
				"",
		);
	}, []);

	useEffect(() => {
		const controller = new AbortController();
		loadUploads(controller.signal).catch((cause: Error) => {
			if (!controller.signal.aborted) setError(cause.message);
		});
		return () => controller.abort();
	}, [loadUploads]);

	useEffect(() => {
		if (!selected) return;
		const controller = new AbortController();
		const { signal } = controller;
		setLoading(true);
		setBalance(null);
		setEntries([]);
		setReports([]);
		setReport(null);
		setSource("");
		setTarget("");
		async function load() {
			try {
				const current = await api<TrialBalance>(`gl/${selected}/status`, {
					signal,
				});
				if (signal.aborted) return;
				setBalance(current);
				if (step === "adjustments" || step === "reports") {
					const drafts = await api<Entry[]>(
						`adjustments?upload_id=${selected}`,
						{ signal },
					);
					if (!signal.aborted) setEntries(drafts);
				}
				if (step === "reports") {
					const items = await api<Report[]>(`reports?upload_id=${selected}`, {
						signal,
					});
					if (!signal.aborted) setReports(items);
				}
			} catch (cause) {
				if (!signal.aborted)
					setError(
						cause instanceof Error ? cause.message : "Không thể tải dữ liệu",
					);
			} finally {
				if (!signal.aborted) setLoading(false);
			}
		}
		void load();
		return () => controller.abort();
	}, [selected, step]);

	async function act(operation: () => Promise<void>) {
		setBusy(true);
		setError("");
		setMessage("");
		try {
			await operation();
		} catch (cause) {
			setError(
				cause instanceof Error ? cause.message : "Yêu cầu không thành công",
			);
		} finally {
			setBusy(false);
		}
	}

	function submit(event: FormEvent, operation: () => Promise<void>) {
		event.preventDefault();
		void act(operation);
	}

	const mappingRows = balance?.mappings ?? [];
	const availableMappings =
		step === "adjustments"
			? mappingRows.filter((row) => row.target_account_code)
			: mappingRows;

	return (
		<section className="mx-auto max-w-5xl space-y-6 p-6">
			<h1 className="text-2xl font-semibold">{titles[step]}</h1>
			<nav aria-label="Các bước xử lý sổ cái" className="flex flex-wrap gap-4">
				{(Object.keys(titles) as Step[]).map((item) => (
					<a
						key={item}
						href={selected ? `${paths[item]}?upload=${selected}` : paths[item]}
						aria-current={item === step ? "page" : undefined}
						className={
							item === step
								? "font-semibold underline"
								: "text-primary underline"
						}
					>
						{titles[item]}
					</a>
				))}
			</nav>

			{error && (
				<p role="alert" className="text-destructive">
					{error}
				</p>
			)}
			{message && <p role="status">{message}</p>}
			{step === "upload" && (
				<form
					className="flex flex-wrap items-end gap-3"
					onSubmit={(event) =>
						submit(event, async () => {
							if (!file) return;
							const data = new FormData();
							data.set("file", file);
							const uploaded = await api<TrialBalance>("gl/upload", {
								method: "POST",
								body: data,
								headers: { "Idempotency-Key": uploadKey.current },
							});
							await loadUploads();
							setSelected(uploaded.id);
							setMessage(`Đã tải ${uploaded.filename}`);
						})
					}
				>
					<label>
						Tệp CSV hoặc XLSX
						<input
							className={field}
							type="file"
							accept=".csv,.xlsx"
							required
							disabled={busy}
							onChange={(event) => {
								setFile(event.target.files?.[0]);
								uploadKey.current = crypto.randomUUID();
							}}
						/>
					</label>
					<button className={button} disabled={busy || !file} type="submit">
						Tải lên và ánh xạ
					</button>
					<button
						className="text-primary underline"
						type="button"
						onClick={downloadTrialBalanceTemplate}
					>
						Tải CSV mẫu
					</button>
				</form>
			)}

			{uploads.length ? (
				<label>
					Bảng cân đối phát sinh
					<select
						className={field}
						value={selected}
						disabled={busy}
						onChange={(event) => {
							setError("");
							setMessage("");
							setSelected(event.target.value);
						}}
					>
						{uploads.map((item) => (
							<option value={item.id} key={item.id}>
								{item.filename}
							</option>
						))}
					</select>
				</label>
			) : (
				step !== "upload" && <p>Hãy tải bảng cân đối phát sinh trước.</p>
			)}
			{loading && <p role="status">Đang tải dữ liệu…</p>}
			{balance && balance.id === selected && (
				<p>
					{balance.row_count} tài khoản · Đã ánh xạ {balance.mapped_count}
				</p>
			)}

			{step === "mappings" && balance && (
				<>
					<div className="max-h-96 overflow-auto">
						<table className="w-full text-left text-sm [&_td]:p-2 [&_th]:p-2">
							<thead>
								<tr>
									<th>Mã VAS</th>
									<th>Tên tài khoản</th>
									<th>Khoản mục IFRS</th>
								</tr>
							</thead>
							<tbody>
								{mappingRows.map((row) => (
									<tr className="border-b" key={row.src_account_code}>
										<td>{row.src_account_code}</td>
										<td>{row.src_account_name}</td>
										<td>{row.target_account_code ?? "Chưa ánh xạ"}</td>
									</tr>
								))}
							</tbody>
						</table>
					</div>
					<form
						className="flex flex-wrap items-end gap-3"
						onSubmit={(event) =>
							submit(event, async () => {
								await api(
									`mappings/${encodeURIComponent(source)}`,
									json("PUT", { ifrs_code: target }),
								);
								setMessage("Đã lưu quy tắc cho các lần tải sau.");
								try {
									setBalance(
										await api<TrialBalance>(`gl/${selected}/remap`, {
											method: "POST",
										}),
									);
									setMessage("Đã lưu quy tắc và cập nhật bảng đang chọn.");
								} catch (cause) {
									setError(
										cause instanceof Error
											? cause.message
											: "Không thể cập nhật bảng đang chọn",
									);
								}
							})
						}
					>
						<label>
							Mã VAS
							<select
								className={field}
								value={source}
								required
								onChange={(event) => setSource(event.target.value)}
							>
								<option value="">Chọn mã</option>
								{availableMappings.map((row) => (
									<option key={row.src_account_code}>
										{row.src_account_code}
									</option>
								))}
							</select>
						</label>
						<label>
							Mã IFRS
							<input
								className={field}
								value={target}
								maxLength={100}
								required
								onChange={(event) => setTarget(event.target.value)}
							/>
						</label>
						<button className={button} disabled={busy} type="submit">
							Lưu quy tắc
						</button>
					</form>
				</>
			)}

			{step === "adjustments" && balance && (
				<>
					<form
						className="space-y-3"
						onSubmit={(event) =>
							submit(event, async () => {
								const body = {
									upload_id: selected,
									source_account: source,
									note,
									lines,
								};
								const entry = await api<Entry>(
									"adjustments",
									json("POST", { ...body, id: keyFor(body) }),
								);
								setEntries((current) => [
									...current.filter((item) => item.id !== entry.id),
									entry,
								]);
								operationKey.current = null;
								setNote("");
								setLines(emptyLines());
								setMessage("Đã lưu bút toán nháp.");
							})
						}
					>
						<label>
							Mã VAS tham chiếu
							<select
								className={field}
								value={source}
								required
								onChange={(event) => setSource(event.target.value)}
							>
								<option value="">Chọn tài khoản đã ánh xạ</option>
								{availableMappings.map((row) => (
									<option key={row.src_account_code}>
										{row.src_account_code}
									</option>
								))}
							</select>
						</label>
						<label>
							Diễn giải
							<textarea
								className={field}
								value={note}
								required
								maxLength={2000}
								onChange={(event) => setNote(event.target.value)}
							/>
						</label>
						{lines.map((line, index) => {
							const change = (values: Partial<Line>) =>
								setLines((current) =>
									current.map((item, at) =>
										at === index ? { ...item, ...values } : item,
									),
								);
							return (
								<div
									className="flex flex-wrap items-end gap-3"
									key={`journal-line-${index}`}
								>
									<label>
										Tài khoản ghi sổ
										<input
											className={field}
											value={line.account}
											required
											maxLength={100}
											onChange={(event) =>
												change({ account: event.target.value })
											}
										/>
									</label>
									<label>
										Bên
										<select
											className={field}
											value={line.type}
											onChange={(event) =>
												change({
													type:
														event.target.value === "debit" ? "debit" : "credit",
												})
											}
										>
											<option value="debit">Nợ</option>
											<option value="credit">Có</option>
										</select>
									</label>
									<label>
										Số tiền
										<input
											className={field}
											value={line.amount}
											required
											inputMode="decimal"
											pattern="[0-9]+([.][0-9]{1,2})?"
											onChange={(event) =>
												change({ amount: event.target.value })
											}
										/>
									</label>
									{index >= 2 && (
										<button
											type="button"
											onClick={() =>
												setLines((current) =>
													current.filter((_, at) => at !== index),
												)
											}
										>
											Xóa dòng
										</button>
									)}
								</div>
							);
						})}
						<div className="flex gap-3">
							<button
								type="button"
								disabled={lines.length >= 100}
								onClick={() =>
									setLines((current) => [
										...current,
										{ account: "", type: "debit", amount: "" },
									])
								}
							>
								Thêm dòng
							</button>
							<button className={button} disabled={busy} type="submit">
								Lưu bút toán nháp
							</button>
						</div>
					</form>
					{entries.map((entry) => (
						<article className="space-y-2 rounded border p-3" key={entry.id}>
							<h2 className="font-semibold">
								{entry.source_account} · {entry.note}
							</h2>
							<ul>
								{entry.lines?.map((line, index) => (
									<li key={`${line.account}-${index}`}>
										{line.type === "debit" ? "Nợ" : "Có"} · {line.account} ·{" "}
										{line.amount}
									</li>
								))}
							</ul>
							{entry.status === "draft" ? (
								<div className="flex gap-3">
									{(["approve", "reject"] as const).map((action) => (
										<button
											key={action}
											className={
												action === "approve" ? button : "px-4 py-2 underline"
											}
											type="button"
											disabled={busy}
											onClick={() =>
												void act(async () => {
													const updated = await api<Entry>(
														`adjustments/${entry.id}/${action}`,
														{ method: "POST" },
													);
													setEntries((current) =>
														current.map((item) =>
															item.id === updated.id ? updated : item,
														),
													);
												})
											}
										>
											{action === "approve" ? "Phê duyệt" : "Từ chối"}
										</button>
									))}
								</div>
							) : (
								<p>
									{entry.status === "approved" ? "Đã phê duyệt" : "Đã từ chối"}
								</p>
							)}
						</article>
					))}
				</>
			)}

			{step === "reports" && balance && (
				<>
					<form
						className="flex flex-wrap items-end gap-3"
						onSubmit={(event) =>
							submit(event, async () => {
								const body = { upload_id: selected, period };
								const created = await api<ReportDetails>(
									"reports/generate",
									json("POST", { ...body, id: keyFor(body) }),
								);
								setReport(created);
								setReports((current) => [
									created,
									...current.filter((item) => item.id !== created.id),
								]);
								operationKey.current = null;
							})
						}
					>
						<label>
							Kỳ báo cáo
							<input
								className={field}
								value={period}
								placeholder="2026-11"
								required
								maxLength={80}
								onChange={(event) => setPeriod(event.target.value)}
							/>
						</label>
						<button
							className={button}
							disabled={
								busy ||
								loading ||
								balance.mapped_count !== balance.row_count ||
								entries.some((entry) => entry.status === "draft")
							}
							type="submit"
						>
							Tạo bảng cân đối sau điều chỉnh
						</button>
					</form>
					{entries.some((entry) => entry.status === "draft") && (
						<p>Còn bút toán nháp cần phê duyệt.</p>
					)}
					{balance.mapped_count !== balance.row_count && (
						<p>Còn tài khoản chưa ánh xạ.</p>
					)}
					{reports.length > 0 && (
						<ul className="space-y-2">
							{reports.map((item) => (
								<li className="flex gap-4" key={item.id}>
									<button
										type="button"
										disabled={busy}
										className="text-primary underline"
										onClick={() =>
											void act(async () =>
												setReport(
													await api<ReportDetails>(`reports/${item.id}`),
												),
											)
										}
									>
										Xem kỳ {item.period}
									</button>
									<a
										className="text-primary underline"
										href={`${base}/reports/${item.id}/download`}
									>
										Tải CSV
									</a>
								</li>
							))}
						</ul>
					)}
					{report && (
						<div className="space-y-2 overflow-auto">
							<h2 className="font-semibold">Kỳ {report.period}</h2>
							<p>
								{report.approved_entry_ids.length} bút toán đã duyệt · Chênh
								lệch Nợ/Có đầu vào {report.source_total}
							</p>
							<table className="w-full text-left text-sm [&_td]:p-2 [&_th]:p-2">
								<thead>
									<tr>
										<th>Tài khoản</th>
										<th>Số dư ánh xạ</th>
										<th>Điều chỉnh</th>
										<th>Số dư sau điều chỉnh</th>
									</tr>
								</thead>
								<tbody>
									{report.rows.map((row) => (
										<tr className="border-b" key={row.account}>
											<td>{row.account}</td>
											<td>{row.mapped_balance}</td>
											<td>{row.adjustment}</td>
											<td>{row.adjusted_balance}</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					)}
				</>
			)}
		</section>
	);
}
