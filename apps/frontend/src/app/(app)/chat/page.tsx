import ChatStream from "@/components/chat/ChatStream";
import { Suspense } from "react";

export default function ChatPage() {
	return (
		<Suspense fallback={null}>
			<ChatStream />
		</Suspense>
	);
}
