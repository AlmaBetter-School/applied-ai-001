"""Maintainer checks: no real API key or external requests are needed."""
import json
from unittest.mock import MagicMock

import httpx
import pytest

import agent
import app
import tools

ORDER_ID = "a" * 32
OTHER_ID = "b" * 32


def record(order_id=ORDER_ID, status="shipped"):
    return {"order_id": order_id, "order_status": status,
            "order_estimated_delivery_date": "2018-06-28 00:00:00",
            "order_delivered_customer_date": None, "customer_id": "private-customer"}


def response(data, status=200):
    return httpx.Response(status, json=data, request=httpx.Request("POST", agent.DEEPSEEK_URL))


def model_reply(tone="empathetic", action="contact_support"):
    return response({"choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps({"tone": tone, "next_step": action})}}]})


@pytest.fixture(autouse=True)
def services(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "  test-key-not-real  ")
    get = MagicMock(return_value=response([record(), record(OTHER_ID, "processing")]))
    post = MagicMock(return_value=model_reply())
    monkeypatch.setattr(tools.httpx, "get", get)
    monkeypatch.setattr(agent.httpx, "post", post)
    return get, post


def test_complete_flow(services):
    get, post = services
    answer, order = agent.resolve("Where is order " + ORDER_ID)
    assert order["status"] == "shipped"
    assert "2018-06-28" in answer
    assert "historical records" in answer
    assert "contact support" in answer
    get.assert_called_once_with(tools.ORDERS_API_URL, timeout=30.0)
    post.assert_called_once()
    request = post.call_args.kwargs
    assert post.call_args.args[0] == agent.DEEPSEEK_URL
    assert request["headers"]["Authorization"] == "Bearer test-key-not-real"
    assert request["json"]["max_tokens"] == 150
    assert request["json"]["thinking"] == {"type": "disabled"}
    assert request["json"]["response_format"] == {"type": "json_object"}
    assert request["json"]["model"] == "deepseek-flash"
    assert "shop's support rules" in request["json"]["messages"][0]["content"]
    assert "private-customer" not in json.dumps(request["json"])


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_key(monkeypatch, services, key):
    if key is None:
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    else:
        monkeypatch.setenv("DEEPSEEK_API_KEY", key)
    answer, order = agent.resolve("Where is order " + ORDER_ID, [])
    assert "DEEPSEEK_API_KEY" in answer
    assert order is None
    for call in services:
        call.assert_not_called()


@pytest.mark.parametrize("message", ["", "  ", "x" * 2001])
def test_invalid_message(services, message):
    assert "1–2,000" in agent.resolve(message)[0]
    for call in services:
        call.assert_not_called()


@pytest.mark.parametrize("message", ["Where is it?", "Order #1003", "a" * 33,
                                          ORDER_ID + " and " + OTHER_ID])
def test_missing_or_ambiguous_order(services, message):
    assert agent.resolve(message)[1] is None
    for call in services:
        call.assert_not_called()


def test_history_is_sent_and_facts_are_refetched(services):
    get, post = services
    history = [{"role": "user", "content": "Where is order " + ORDER_ID},
               {"role": "assistant", "content": "Previously recorded as delivered."}]
    for question in ["What should I do?", "I need it for class."]:
        answer, order = agent.resolve(question, history)
        assert order["status"] == "shipped"
        context = json.loads(post.call_args.kwargs["json"]["messages"][1]["content"])
        assert context["history"] == history
        assert context["customer_request"] == question
        assert context["verified_order"]["status"] == "shipped"
    assert get.call_count == 2
    assert len(history) == 2


@pytest.mark.parametrize("message,expected", [
    ("Check " + OTHER_ID, OTHER_ID), ("What now?", ORDER_ID),
    ("Check " + ORDER_ID.upper(), ORDER_ID),
])
def test_latest_customer_order(message, expected):
    history = [{"role": "user", "content": "Check " + ORDER_ID},
               {"role": "assistant", "content": "Order " + OTHER_ID}]
    assert agent.resolve(message, history)[1]["order_id"] == expected


def test_assistant_cannot_supply_order_id(services):
    assert agent.resolve("What now?", [{"role": "assistant", "content": ORDER_ID}])[1] is None
    services[0].assert_not_called()


def test_ambiguous_recent_order_is_not_replaced_by_older_one(services):
    history = [{"role": "user", "content": ORDER_ID},
               {"role": "user", "content": ORDER_ID + " " + OTHER_ID}]
    assert agent.resolve("What now?", history)[1] is None
    services[0].assert_not_called()


def test_history_limit(services):
    history = [{"role": "user", "content": ORDER_ID}]
    history += [{"role": "user", "content": "Hello"}] * 12
    assert agent.resolve("What now?", history)[1] is None
    agent.resolve("Check " + ORDER_ID, history)
    context = json.loads(services[1].call_args.kwargs["json"]["messages"][1]["content"])
    assert len(context["history"]) == 12


def test_unknown_order(services):
    assert "could not find" in agent.resolve("Check " + "c" * 32)[0]
    services[1].assert_not_called()


@pytest.mark.parametrize("rows", [{}, [None], [record(), record()],
                                      [dict(record(), order_status="invented")],
                                      [dict(record(), order_estimated_delivery_date="tomorrow")],
                                      [dict(record(), order_delivered_customer_date=123)],
                                      [{"order_id": ORDER_ID}]])
def test_bad_records_are_not_sent_to_model(services, rows):
    services[0].return_value = response(rows)
    answer, order = agent.resolve("Check " + ORDER_ID)
    assert "cannot check" in answer
    assert order is None
    services[1].assert_not_called()


def test_missing_dates(services):
    services[0].return_value = response([dict(record(), order_estimated_delivery_date=None)])
    answer, order = agent.resolve("Check " + ORDER_ID)
    assert order["expected_delivery"] is None
    assert "not available" in answer


@pytest.mark.parametrize("status", tools.ORDER_STATUSES)
def test_status_policy_overrides(services, status):
    services[0].return_value = response([record(status=status)])
    services[1].return_value = model_reply(action="check_delivery")
    answer, order = agent.resolve("Check " + ORDER_ID)
    assert order["status"] == status
    if status in ("canceled", "unavailable"):
        assert "contact support" in answer
    elif status == "delivered":
        assert "delivery location" in answer
    else:
        assert "current update" in answer


@pytest.mark.parametrize("status,fragment", [(401, "accept the key"), (402, "balance or usage"),
                                                (429, "balance or usage"), (503, "unavailable")])
def test_deepseek_http_errors(services, status, fragment):
    services[1].return_value = response({"error": "never display private details"}, status)
    answer, order = agent.resolve("Check " + ORDER_ID)
    assert fragment in answer
    assert "private details" not in answer
    assert "test-key" not in answer
    assert order is not None


@pytest.mark.parametrize("content", ["", "not json", "null", "[]",
    '{"tone":"friendly","next_step":"track"}',
    '{"tone":"neutral","next_step":"refund"}',
    '{"tone":"neutral"}', '{"tone":"neutral","next_step":[]}'])
def test_bad_model_output(services, content):
    services[1].return_value = response({"choices": [{"finish_reason": "stop", "message": {"content": content}}]})
    assert "reliable reply" in agent.resolve("Check " + ORDER_ID)[0]


@pytest.mark.parametrize("body", [{}, {"choices": []}, {"choices": [{"finish_reason": "length"}]}])
def test_incomplete_response(services, body):
    services[1].return_value = response(body)
    assert "reliable reply" in agent.resolve("Check " + ORDER_ID)[0]


@pytest.mark.parametrize("which", [0, 1])
def test_network_failure(services, which):
    services[which].side_effect = httpx.ConnectError("private network details")
    answer, order = agent.resolve("Check " + ORDER_ID)
    assert "private network" not in answer
    assert (order is None) == (which == 0)


def test_ui_followup_reset_and_missing_order(services):
    _, chat, history, card = app.reply("Where is order " + ORDER_ID, [])
    assert "Shipped" in card
    assert len(chat) == 2
    _, chat, history, card = app.reply("I need it for class. What now?", history)
    assert len(chat) == 4
    context = json.loads(services[1].call_args.kwargs["json"]["messages"][1]["content"])
    assert len(context["history"]) == 2
    _, _, history, card = app.reply("Check " + "c" * 32, history)
    assert card == app.EMPTY_ORDER
    message, chat, history, card = app.reset_chat()
    assert message == "" and chat == [] and history == []
    assert card == app.EMPTY_ORDER
    _, _, history, _ = app.reply("What now?", history)
    assert "order number" in history[-1]["content"]


def test_ui_keeps_visitors_separate():
    first_history = []
    _, _, updated, _ = app.reply("Check " + ORDER_ID, first_history)
    assert first_history == []
    assert len(updated) == 2
    _, _, second, _ = app.reply("What now?", [])
    assert "order number" in second[-1]["content"]


def test_empty_ui_message_does_not_call_services(services):
    _, chat, history, update = app.reply("   ", [])
    assert chat == [] and history == []
    assert update == {"__type__": "update"}
    for call in services:
        call.assert_not_called()
