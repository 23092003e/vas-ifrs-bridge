"use client";

import { useEffect, useRef } from "react";

interface Beam {
	x: number;
	y: number;
	length: number;
	speed: number;
	vertical: boolean;
	direction: 1 | -1;
	color: string;
	alpha: number;
	maxAlpha: number;
}

interface Particle {
	x: number;
	y: number;
	vx: number;
	vy: number;
	radius: number;
	alpha: number;
	baseAlpha: number;
}

export function LandingBackground() {
	const containerRef = useRef<HTMLDivElement>(null);
	const canvasRef = useRef<HTMLCanvasElement>(null);

	useEffect(() => {
		const canvas = canvasRef.current;
		const container = containerRef.current;
		if (!canvas || !container) return;

		const ctx = canvas.getContext("2d");
		if (!ctx) return;

		let animationId: number;
		canvas.width = window.innerWidth;
		canvas.height = window.innerHeight;
		let width = canvas.width;
		let height = canvas.height;

		// Track mouse for gentle interactivity
		const mouse = { x: width / 2, y: height * 0.3, active: false };

		const handleResize = () => {
			if (!canvas) return;
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
			width = canvas.width;
			height = canvas.height;
		};

		const handleMouseMove = (e: MouseEvent) => {
			mouse.x = e.clientX;
			mouse.y = e.clientY;
			mouse.active = true;
			container.style.setProperty("--mouse-x", `${e.clientX}px`);
			container.style.setProperty("--mouse-y", `${e.clientY}px`);
		};

		window.addEventListener("resize", handleResize, { passive: true });
		window.addEventListener("mousemove", handleMouseMove, { passive: true });

		// Grid configuration
		const gridSize = 48;

		// Color palette for beams (Subtle financial tech tones)
		const beamColors = [
			"rgba(56, 114, 224, ", // Slate / Sapphire
			"rgba(16, 185, 129, ", // Emerald / IFRS
			"rgba(99, 102, 241, ", // Indigo / RAG
		];

		// Initialize Beams
		const beams: Beam[] = [];
		const maxBeams = 14;

		const createBeam = (): Beam => {
			const vertical = Math.random() > 0.5;
			const direction = Math.random() > 0.5 ? 1 : -1;
			const color = beamColors[Math.floor(Math.random() * beamColors.length)];
			const maxAlpha = 0.22 + Math.random() * 0.32; // Soft subliminal brightness

			if (vertical) {
				const col = Math.floor(Math.random() * (width / gridSize));
				const x = col * gridSize;
				const y = direction === 1 ? -60 : height + 60;
				return {
					x,
					y,
					length: 80 + Math.random() * 120,
					speed: (1.2 + Math.random() * 1.8) * direction,
					vertical: true,
					direction,
					color,
					alpha: 0,
					maxAlpha,
				};
			}

			const row = Math.floor(Math.random() * (height / gridSize));
			const y = row * gridSize;
			const x = direction === 1 ? -60 : width + 60;
			return {
				x,
				y,
				length: 80 + Math.random() * 120,
				speed: (1.2 + Math.random() * 1.8) * direction,
				vertical: false,
				direction,
				color,
				alpha: 0,
				maxAlpha,
			};
		};

		for (let i = 0; i < maxBeams; i++) {
			const beam = createBeam();
			// Distribute initial positions
			if (beam.vertical) {
				beam.y = Math.random() * height;
			} else {
				beam.x = Math.random() * width;
			}
			beam.alpha = Math.random() * beam.maxAlpha;
			beams.push(beam);
		}

		// Floating Ledger Micro-Particles
		const particles: Particle[] = [];
		const particleCount = 28;
		for (let i = 0; i < particleCount; i++) {
			const baseAlpha = 0.15 + Math.random() * 0.25;
			particles.push({
				x: Math.random() * width,
				y: Math.random() * height,
				vx: (Math.random() - 0.5) * 0.4,
				vy: (Math.random() - 0.5) * 0.4,
				radius: 1 + Math.random() * 1.5,
				alpha: baseAlpha,
				baseAlpha,
			});
		}

		// Animation Loop
		const render = () => {
			ctx.clearRect(0, 0, width, height);

			// 1. Draw Subtle Static Grid Lines
			ctx.lineWidth = 1;
			ctx.strokeStyle = "rgba(148, 163, 184, 0.08)";

			// Vertical grid lines
			for (let x = 0; x <= width; x += gridSize) {
				ctx.beginPath();
				ctx.moveTo(x, 0);
				ctx.lineTo(x, height);
				ctx.stroke();
			}

			// Horizontal grid lines
			for (let y = 0; y <= height; y += gridSize) {
				ctx.beginPath();
				ctx.moveTo(0, y);
				ctx.lineTo(width, y);
				ctx.stroke();
			}

			// 2. Animate and Draw Traveling Light Beams
			for (let i = 0; i < beams.length; i++) {
				const b = beams[i];

				if (b.vertical) {
					b.y += b.speed;
					if (b.alpha < b.maxAlpha) b.alpha += 0.01;

					const grad = ctx.createLinearGradient(
						b.x,
						b.y - (b.direction === 1 ? b.length : -b.length),
						b.x,
						b.y,
					);
					grad.addColorStop(0, `${b.color}0)`);
					grad.addColorStop(1, `${b.color}${b.alpha})`);

					ctx.lineWidth = 1.8;
					ctx.strokeStyle = grad;
					ctx.beginPath();
					ctx.moveTo(b.x, b.y - (b.direction === 1 ? b.length : -b.length));
					ctx.lineTo(b.x, b.y);
					ctx.stroke();

					// Sparkle at beam head
					ctx.fillStyle = `${b.color}${b.alpha * 1.2})`;
					ctx.beginPath();
					ctx.arc(b.x, b.y, 2, 0, Math.PI * 2);
					ctx.fill();

					// Respawn if off screen
					if (
						(b.direction === 1 && b.y > height + 80) ||
						(b.direction === -1 && b.y < -80)
					) {
						beams[i] = createBeam();
					}
				} else {
					b.x += b.speed;
					if (b.alpha < b.maxAlpha) b.alpha += 0.01;

					const grad = ctx.createLinearGradient(
						b.x - (b.direction === 1 ? b.length : -b.length),
						b.y,
						b.x,
						b.y,
					);
					grad.addColorStop(0, `${b.color}0)`);
					grad.addColorStop(1, `${b.color}${b.alpha})`);

					ctx.lineWidth = 1.8;
					ctx.strokeStyle = grad;
					ctx.beginPath();
					ctx.moveTo(b.x - (b.direction === 1 ? b.length : -b.length), b.y);
					ctx.lineTo(b.x, b.y);
					ctx.stroke();

					// Sparkle at beam head
					ctx.fillStyle = `${b.color}${b.alpha * 1.2})`;
					ctx.beginPath();
					ctx.arc(b.x, b.y, 2, 0, Math.PI * 2);
					ctx.fill();

					// Respawn if off screen
					if (
						(b.direction === 1 && b.x > width + 80) ||
						(b.direction === -1 && b.x < -80)
					) {
						beams[i] = createBeam();
					}
				}
			}

			// 3. Animate and Draw Micro-Particles
			for (let i = 0; i < particles.length; i++) {
				const p = particles[i];
				p.x += p.vx;
				p.y += p.vy;

				// Wrap around edges
				if (p.x < 0) p.x = width;
				if (p.x > width) p.x = 0;
				if (p.y < 0) p.y = height;
				if (p.y > height) p.y = 0;

				// Gentle mouse interaction
				if (mouse.active) {
					const dx = mouse.x - p.x;
					const dy = mouse.y - p.y;
					const dist = Math.sqrt(dx * dx + dy * dy);
					if (dist < 100) {
						p.x -= (dx / dist) * 0.8;
						p.y -= (dy / dist) * 0.8;
					}
				}

				ctx.fillStyle = `rgba(56, 114, 224, ${p.alpha})`;
				ctx.beginPath();
				ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
				ctx.fill();
			}

			animationId = requestAnimationFrame(render);
		};

		render();

		return () => {
			cancelAnimationFrame(animationId);
			window.removeEventListener("resize", handleResize);
			window.removeEventListener("mousemove", handleMouseMove);
		};
	}, []);

	return (
		<div ref={containerRef} className="landing-bg-layer" aria-hidden="true">
			{/* Linear / Stripe Style Aurora Ambient Mesh Glow */}
			<div className="landing-aurora-mesh" />

			{/* High-Performance Canvas with Grid Beams & Micro Particles */}
			<canvas ref={canvasRef} className="landing-canvas-beams" />

			{/* Interactive Soft Cursor Spotlight */}
			<div className="bg-cursor-spotlight" />

			{/* Radial Vignette Mask */}
			<div className="bg-vignette" />
		</div>
	);
}
