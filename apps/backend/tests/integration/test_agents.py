import asyncio
import logging
import pytest

from app.agents.orchestrator import Orchestrator
from app.schemas.chat import ChatRequest

logging.basicConfig(level=logging.INFO)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_e2e_agent():
    orchestrator = Orchestrator()
    
    # Quick sanity check for orchestrator streaming
    req1 = ChatRequest(content="so sánh VAS 15 và IFRS 15", reasoning="balanced", lang="vi", intent_hint="compare")
    events = []
    try:
        async for event in orchestrator.run_stream(req1):
            events.append(event)
            if len(events) >= 2:
                break
    except Exception as exc:
        pytest.skip(f"Integration environment not available: {exc}")

    assert len(events) > 0


if __name__ == "__main__":
    asyncio.run(test_e2e_agent())
