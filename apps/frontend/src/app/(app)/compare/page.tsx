"use client";

import {
	CompareStreamView,
	type PresetTopic,
	RelationCard,
	StandardSelector,
	TopicPresets,
} from "@/components/compare";
import { applyStreamEvent, consumeSseBuffer } from "@/lib/chat/events";
import type { Message, SSEEvent } from "@/types/api";
import type { RelationItem, StandardsData } from "@/types/compare";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export default function ComparePage() {
	const [standardsData, setStandardsData] = useState<StandardsData>({
		vas_standards: [],
		ifrs_standards: [],
		relations: [],
		topics: [],
	});
	const [selectedVas, setSelectedVas] = useState<string>("VAS-14");
	const [selectedIfrs, setSelectedIfrs] = useState<string>("IFRS-15");
	const [focusQuery, setFocusQuery] = useState<string>("");

	const [comparisonMessage, setComparisonMessage] = useState<Message>({
		id: "compare-res",
		role: "assistant",
		content: "",
		citations: [],
		loading: false,
	});
	const [error, setError] = useState<string | null>(null);

	const abortRef = useRef<AbortController | null>(null);

	// Load standards catalog on mount
	useEffect(() => {
		const controller = new AbortController();
		async function loadStandards() {
			try {
				const res = await fetch("/api/compare/standards", {
					signal: controller.signal,
				});
				if (res.ok) {
					const data = (await res.json()) as StandardsData;
					setStandardsData(data);
				}
			} catch (err) {
				if (!controller.signal.aborted) {
					console.warn("Failed to fetch standards list", err);
				}
			}
		}
		void loadStandards();
		return () => controller.abort();
	}, []);

	// Matched relation from ontology if existing
	const currentRelation = useMemo<RelationItem | null>(() => {
		if (!standardsData.relations || standardsData.relations.length === 0) {
			return null;
		}
		return (
			standardsData.relations.find(
				(rel) => rel.vas === selectedVas && rel.ifrs === selectedIfrs,
			) || null
		);
	}, [standardsData.relations, selectedVas, selectedIfrs]);

	const handleSelectPreset = (preset: PresetTopic) => {
		setSelectedVas(preset.vas);
		setSelectedIfrs(preset.ifrs);
		setFocusQuery(preset.focusHint);
		setError(null);
	};

	const handleReset = () => {
		abortRef.current?.abort();
		setSelectedVas("VAS-14");
		setSelectedIfrs("IFRS-15");
		setFocusQuery("");
		setError(null);
		setComparisonMessage({
			id: "compare-res",
			role: "assistant",
			content: "",
			citations: [],
			loading: false,
		});
	};

	const handleCompare = useCallback(async () => {
		abortRef.current?.abort();
		const controller = new AbortController();
		abortRef.current = controller;

		setError(null);
		setComparisonMessage({
			id: "compare-res",
			role: "assistant",
			content: "",
			citations: [],
			loading: true,
		});

		const promptContent = `So sánh chi tiết chuẩn mực kế toán ${selectedVas} và ${selectedIfrs}.${
			focusQuery ? ` Trọng tâm đối chiếu: ${focusQuery}` : ""
		} Hãy nêu rõ: 1. Phạm vi & mục tiêu; 2. Nguyên tắc ghi nhận & đo lường cốt lõi; 3. Bảng khác biệt trọng yếu giữa VAS và IFRS; 4. Ảnh hưởng đến BCTC và các bút toán chuyển đổi cần lưu ý. Kèm trích dẫn điều khoản chính xác.`;

		try {
			const res = await fetch("/api/chat/stream", {
				method: "POST",
				headers: {
					Accept: "text/event-stream",
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					content: promptContent,
					intent_hint: "compare",
					lang: "vi",
					scope: "shared",
					reasoning: "balanced",
				}),
				signal: controller.signal,
			});

			if (!res.ok) {
				const errorDetail = await res.text();
				throw new Error(errorDetail || `HTTP ${res.status}`);
			}

			if (!res.body) {
				throw new Error("Không nhận được luồng dữ liệu phản hồi.");
			}

			const reader = res.body.getReader();
			const decoder = new TextDecoder();
			let buffer = "";

			const handleEvent = (event: SSEEvent) => {
				setComparisonMessage((prev) => applyStreamEvent(prev, event));
			};

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;
				buffer += decoder.decode(value, { stream: true });
				const consumed = consumeSseBuffer(buffer);
				buffer = consumed.rest;
				for (const ev of consumed.events) handleEvent(ev);
			}

			buffer += decoder.decode();
			const finalConsumed = consumeSseBuffer(buffer, true);
			for (const ev of finalConsumed.events) handleEvent(ev);
		} catch (err: unknown) {
			if (controller.signal.aborted) return;
			const msg = err instanceof Error ? err.message : String(err);
			console.error("Comparison stream failed", err);
			setError(msg);
			setComparisonMessage((prev) => ({
				...prev,
				loading: false,
			}));
		} finally {
			if (abortRef.current === controller) {
				abortRef.current = null;
				setComparisonMessage((prev) => ({ ...prev, loading: false }));
			}
		}
	}, [selectedVas, selectedIfrs, focusQuery]);

	return (
		<div className="page-shell">
			{/* Page Header */}
			<div className="page-hd">
				<div className="page-hd-rule" />
				<h1>So sánh VAS & IFRS</h1>
				<p>
					Đối chiếu nguyên tắc ghi nhận, đo lường và trình bày giữa Chuẩn mực kế
					toán Việt Nam (VAS) và Chuẩn mực báo cáo tài chính quốc tế (IFRS/IAS).
				</p>
			</div>

			{/* Page Body */}
			<div className="page-body" style={{ maxWidth: 1100, margin: "0 auto" }}>
				{/* Preset Quick Chips */}
				<TopicPresets
					selectedVas={selectedVas}
					selectedIfrs={selectedIfrs}
					onSelectPreset={handleSelectPreset}
				/>

				{/* Standard Selection Controls */}
				<StandardSelector
					vasList={standardsData.vas_standards}
					ifrsList={standardsData.ifrs_standards}
					selectedVas={selectedVas}
					selectedIfrs={selectedIfrs}
					focusQuery={focusQuery}
					loading={comparisonMessage.loading ?? false}
					onVasChange={setSelectedVas}
					onIfrsChange={setSelectedIfrs}
					onFocusQueryChange={setFocusQuery}
					onCompare={handleCompare}
					onReset={handleReset}
				/>

				{/* Instant Ontology Differences Card if matched */}
				<RelationCard
					relation={currentRelation}
					vasCode={selectedVas}
					ifrsCode={selectedIfrs}
				/>

				{/* Streaming RAG Comparison Output */}
				<CompareStreamView
					vasCode={selectedVas}
					ifrsCode={selectedIfrs}
					content={comparisonMessage.content}
					citations={comparisonMessage.citations}
					loading={comparisonMessage.loading ?? false}
					error={error}
					onRetry={handleCompare}
				/>
			</div>
		</div>
	);
}
