/** @type {import('next').NextConfig} */
const allowedOrigins = (
	process.env.SERVER_ACTION_ALLOWED_ORIGINS ?? "localhost:3000"
)
	.split(",")
	.map((origin) => origin.trim())
	.filter(Boolean);

const nextConfig = {
	output: "standalone",
	experimental: { serverActions: { allowedOrigins } },
};
export default nextConfig;
