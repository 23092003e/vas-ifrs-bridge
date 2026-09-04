import ChatStream from "@/components/chat/ChatStream";
import { Suspense } from "react";

export default function ConversationPage() {
	return (
		<Suspense fallback={null}>
			<ChatStream />
		</Suspense>
	);
}
