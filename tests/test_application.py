import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from streamlit.testing.v1 import AppTest

import agent
import tools
from models import Resolution, Understanding


@pytest.fixture
def orders_api(monkeypatch):
    records = [
        {"order_id": order_id, "order_status": status,
         "order_estimated_delivery_date": "2018-06-28 00:00:00",
         "order_delivered_customer_date": None, "customer_id": "not-for-model"}
        for order_id, status in [("a" * 32, "shipped"), ("b" * 32, "processing"),
                                  ("c" * 32, "canceled"), ("d" * 32, "delivered")]
    ]
    records[-1]["order_delivered_customer_date"] = "2018-06-20 12:00:00"
    def get(url, **kwargs):
        assert url == tools.ORDERS_API_URL
        assert kwargs["timeout"] == 30.0
        return httpx.Response(200, json=records, request=httpx.Request("GET", url))
    monkeypatch.setattr(tools.httpx, "get", get)


@pytest.fixture
def model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-not-a-real-key")
    client = MagicMock()
    client.__enter__.return_value = client
    monkeypatch.setattr(agent.genai, "Client", lambda **kwargs: client)
    return client.models.generate_content


def model_answers(model, order_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", action="contact_support"):
    model.side_effect = [
        SimpleNamespace(text=Understanding(intent="order_status", order_id=order_id).model_dump_json()),
        SimpleNamespace(text=Resolution(tone="empathetic", next_step=action).model_dump_json()),
    ]


@pytest.mark.parametrize("order_id,status", [
    ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "shipped"), ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "processing"),
    ("cccccccccccccccccccccccccccccccc", "canceled"), ("dddddddddddddddddddddddddddddddd", "delivered"),
])
def test_dataset_flow(orders_api, model, order_id, status):
    model_answers(model, order_id, "track")
    reply = agent.resolve(f"Where is order #{order_id}?")
    assert reply.order.status == status
    assert reply.order.expected_delivery == date(2018, 6, 28)
    assert reply.order.latest_update in reply.message
    assert reply.status == "Order checked"
    context = json.loads(model.call_args.kwargs["contents"])
    assert context["verified_order"]["order_id"] == order_id
    assert "customer_id" not in context["verified_order"]
    assert "dataset records" in reply.message
    assert "Customer support policy" in model.call_args.kwargs["config"].system_instruction
    assert model.call_args.kwargs["config"].response_mime_type == "application/json"
    if status == "canceled":
        assert "contact the support team" in reply.message
    if status == "delivered":
        assert "check the delivery location" in reply.message


def test_unknown_order(orders_api, model):
    model_answers(model, "ffffffffffffffffffffffffffffffff")
    assert agent.resolve("Where is order #ffffffffffffffffffffffffffffffff?").status == "Not found"
    assert model.call_count == 1


@pytest.mark.parametrize("order_id,message", [
    (None, "Where is my parcel?"), ("ffffffffffffffffffffffffffffffff", "Where is order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa?"),
    ("../aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "order ../aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"), ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa0"),
])
def test_invalid_extraction_never_calls_tool(monkeypatch, model, order_id, message):
    model_answers(model, order_id)
    lookup = MagicMock()
    monkeypatch.setattr(agent, "get_order_status", lookup)
    assert agent.resolve(message).status == "Needs input"
    lookup.assert_not_called()


def test_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").status == "Setup needed"


@pytest.mark.parametrize("message", ["", " ", "x" * 2001])
def test_invalid_input(message):
    assert agent.resolve(message).status == "Needs input"


def test_model_refusal(model):
    model.return_value = SimpleNamespace(text=None)
    assert agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").status == "Needs input"


def test_second_model_refusal(orders_api, model):
    model.side_effect = [
        SimpleNamespace(text=Understanding(intent="order_status", order_id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").model_dump_json()),
        SimpleNamespace(text=None),
    ]
    reply = agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    assert reply.status == "Try again"
    assert reply.order.order_id == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def test_model_connection_failure(model):
    model.side_effect = httpx.ConnectError("connection failed")
    assert agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").status == "Assistant unavailable"


@pytest.mark.parametrize("payload", [
    {"order_id": "ffffffffffffffffffffffffffffffff", "status": "shipped", "expected_delivery": None, "latest_update": "Update"},
    {"order_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "status": "invented", "expected_delivery": None, "latest_update": "Update"},
    {"order_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},
])
def test_invalid_api_response(monkeypatch, payload):
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=payload, request=httpx.Request("GET", "https://example.test")))
    with pytest.raises(tools.OrdersUnavailable):
        tools.get_order_status("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")


@pytest.mark.parametrize("status", [429, 500])
def test_api_http_failure(monkeypatch, model, status):
    model_answers(model)
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: httpx.Response(
        status, request=httpx.Request("GET", "https://example.test")))
    reply = agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
    assert reply.status == "Orders unavailable"
    assert reply.order is None
    assert model.call_count == 1


def test_api_timeout(monkeypatch, model):
    model_answers(model)
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout("timed out")
    monkeypatch.setattr(tools.httpx, "get", timeout)
    assert agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").status == "Orders unavailable"


def test_non_json_api_response(monkeypatch):
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: httpx.Response(
        200, text="not JSON", request=httpx.Request("GET", "https://example.test")))
    with pytest.raises(tools.OrdersUnavailable):
        tools.get_order_status("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")


def test_streamlit_chat_and_stale_card(orders_api, model):
    model_answers(model)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run()
    assert not app.exception
    assert app.title[0].value == "AI Support Resolution Agent"
    app.chat_input[0].set_value("My order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa hasn't arrived.").run()
    assert not app.exception
    assert app.metric[0].value == "Shipped"
    model_answers(model, "ffffffffffffffffffffffffffffffff")
    app.chat_input[0].set_value("Where is order #ffffffffffffffffffffffffffffffff?").run()
    assert not app.exception
    assert not app.metric
    app.button[0].click().run()
    assert not app.session_state["messages"]


def test_journey_entrypoint_and_steps():
    root = Path(__file__).parents[1]
    instructions = (root / "AGENTS.md").read_text()
    assert '"Start my AlmaBetter project"' in instructions
    for path in [".almabetter/project.md", ".almabetter/conversation-level.md"]:
        assert path in instructions
        assert (root / path).is_file()
    journey = (root / ".almabetter/project.md").read_text()
    for number in range(1, 9):
        assert f"Record Step `{number:02}`" in journey
    assert "register_student_form()" in journey
    assert "start_project(student_session_id" in journey
    assert "priority" not in Understanding.model_fields


@pytest.mark.parametrize("content", ["not JSON", '{"intent":"invalid","order_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'])
def test_invalid_gemini_output(model, content):
    model.return_value = SimpleNamespace(text=content)
    assert agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").status == "Assistant unavailable"


def test_gemini_api_error(model):
    from google.genai.errors import ClientError
    model.side_effect = ClientError(429, {"error": {"message": "Quota exceeded"}})
    assert agent.resolve("Order #aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").status == "Assistant unavailable"


@pytest.mark.parametrize("status", ["approved", "canceled", "created", "delivered", "invoiced", "processing", "shipped", "unavailable"])
def test_all_dataset_statuses(monkeypatch, status):
    row = {"order_id": "a" * 32, "order_status": status,
           "order_estimated_delivery_date": None, "order_delivered_customer_date": None}
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=[row], request=httpx.Request("GET", tools.ORDERS_API_URL)))
    order = tools.get_order_status("a" * 32)
    assert order.status == status
    assert order.expected_delivery is None
    assert order.latest_update == "No customer delivery timestamp recorded."


@pytest.mark.parametrize("field,value", [
    ("order_status", "invented"), ("order_estimated_delivery_date", "not a date"),
    ("order_delivered_customer_date", "not a date"),
])
def test_malformed_matching_record(monkeypatch, field, value):
    row = {"order_id": "a" * 32, "order_status": "shipped",
           "order_estimated_delivery_date": None, "order_delivered_customer_date": None}
    row[field] = value
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=[row], request=httpx.Request("GET", tools.ORDERS_API_URL)))
    with pytest.raises(tools.OrdersUnavailable):
        tools.get_order_status("a" * 32)


def test_duplicate_ids_rejected(monkeypatch):
    rows = [{"order_id": "a" * 32}] * 2
    monkeypatch.setattr(tools.httpx, "get", lambda *a, **k: httpx.Response(
        200, json=rows, request=httpx.Request("GET", tools.ORDERS_API_URL)))
    with pytest.raises(tools.OrdersUnavailable):
        tools.get_order_status("a" * 32)


def test_uppercase_order_id(orders_api, model):
    model_answers(model, "A" * 32)
    assert agent.resolve("Where is order " + "A" * 32).order.order_id == "a" * 32


def test_followup_sends_history_and_refetches(orders_api, model, monkeypatch):
    history = [{"role": "user", "content": "Where is order " + "a" * 32},
               {"role": "assistant", "content": "Previously recorded as delivered."}]
    lookup = MagicMock(wraps=tools.get_order_status)
    monkeypatch.setattr(agent, "get_order_status", lookup)
    model_answers(model, "a" * 32)
    reply = agent.resolve("What can I do about it?", history)
    assert reply.order.status == "shipped"
    lookup.assert_called_once_with("a" * 32)
    for call in model.call_args_list:
        context = json.loads(call.kwargs["contents"])
        assert context["history"] == history
        assert context["customer_request"] == "What can I do about it?"
    assert len(history) == 2  # The caller's history is not modified.


@pytest.mark.parametrize("new_message,chosen_id,accepted", [
    ("Where is order " + "b" * 32, "b" * 32, True),
    ("Where is order " + "b" * 32, "a" * 32, False),
    ("Compare " + "a" * 32 + " and " + "b" * 32, "a" * 32, False),
])
def test_current_order_precedence(orders_api, model, new_message, chosen_id, accepted):
    model_answers(model, chosen_id)
    reply = agent.resolve(new_message, [{"role": "user", "content": "Order " + "a" * 32}])
    assert (reply.status == "Order checked") is accepted
    if not accepted:
        assert reply.status == "Needs input"


def test_assistant_cannot_introduce_order_id(model):
    model_answers(model, "a" * 32)
    reply = agent.resolve("What about that order?", [
        {"role": "assistant", "content": "Order " + "a" * 32}])
    assert reply.status == "Needs input"
    assert model.call_count == 1


def test_history_limit(model):
    history = [{"role": "user", "content": "Order " + "a" * 32}]
    history += [{"role": "user", "content": "Hello"}] * 12
    model_answers(model, "a" * 32)
    assert agent.resolve("Where is it?", history).status == "Needs input"
    sent = json.loads(model.call_args.kwargs["contents"])["history"]
    assert len(sent) == 12
    assert all("a" * 32 not in turn["content"] for turn in sent)


def test_ui_followup_and_reset(orders_api, model):
    app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run()
    model_answers(model, "a" * 32)
    app.chat_input[0].set_value("Where is order " + "a" * 32).run()
    model_answers(model, "a" * 32)
    app.chat_input[0].set_value("What can I do about it?").run()
    assert not app.exception
    assert app.session_state["reply"].order.order_id == "a" * 32
    assert len(json.loads(model.call_args.kwargs["contents"])["history"]) == 2
    app.button[0].click().run()
    model_answers(model, "a" * 32)
    app.chat_input[0].set_value("What about my order?").run()
    assert not app.exception
    assert app.session_state["reply"].status == "Needs input"
    assert json.loads(model.call_args.kwargs["contents"])["history"] == []
