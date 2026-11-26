from app.rag import ontology_service


def test_expand_query_is_ordered_and_deduplicated(monkeypatch):
    topic = {
        "topic_id": "inventory",
        "topic_name": "Inventory",
        "aliases": ["Hàng tồn kho", "nrv"],
    }
    monkeypatch.setattr(ontology_service, "_TOPICS", [topic])
    monkeypatch.setattr(
        ontology_service,
        "_TERMS",
        [{"topic_id": "inventory", "term": "nrv", "aliases": ["fifo"]}],
    )
    monkeypatch.setattr(
        ontology_service, "_RELATIONS", [{"topic": "Inventory", "ias": "IAS-2"}]
    )

    assert ontology_service.expand_query("Hàng tồn kho", [topic]) == (
        "Hàng tồn kho IAS 2 IAS-2 Inventory fifo nrv"
    )
