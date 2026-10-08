"""The screen: a conversation on the left, order details on the right."""
import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from agent import resolve

load_dotenv(Path(__file__).with_name(".env"))
EMPTY_ORDER = "### Your order\nOrder details will appear here after a successful lookup."


def reply(message, history):
    """Ask the agent, remember the exchange, and update the order card."""
    if not message.strip():
        return "", history, history, gr.skip()
    answer, order = resolve(message, history)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    details = EMPTY_ORDER
    if order:
        details = (
            f"### Your order\n**{order['status'].title()}**\n\n"
            f"Order number\n`{order['order_id']}`\n\n"
            f"**Estimated delivery**\n{order['expected_delivery'] or 'Not recorded'}\n\n"
            f"**Delivered on**\n{order['delivered_on'] or 'Not recorded'}\n\n"
            "*Historical records · not live tracking*"
        )
    return "", history, history, details


def reset_chat():
    return "", [], [], EMPTY_ORDER


# Blocks arranges the screen. State keeps a separate conversation for each visitor.
with gr.Blocks(title="Order Support", analytics_enabled=False) as demo:
    gr.Markdown("ALMABETTER · APPLIED AI WORKSHOP", elem_id="eyebrow")
    gr.Markdown("# A little clarity for your delivery.\n"
                "Check a parcel, ask a follow-up, and find your next step.")
    history = gr.State([])
    with gr.Row():
        with gr.Column(scale=3):
            chat = gr.Chatbot(
                label="Your conversation", height=390, layout="bubble",
                placeholder="Ask about an order to get started.",
                render_markdown=False, buttons=["copy"],
            )
            message = gr.Textbox(label="Your message", placeholder="Where is my order?",
                                 lines=1, max_lines=3)
            with gr.Row():
                send = gr.Button("Send message", variant="primary")
                clear = gr.Button("Start a new conversation")
            gr.Examples(
                examples=[["Where is order ee64d42b8cf066f35eac1cf57de1aa85?"]],
                inputs=message, label="Try a practice order",
            )
        with gr.Column(scale=1, min_width=260, variant="panel"):
            order_card = gr.Markdown(EMPTY_ORDER)
            gr.Markdown("---\n### Keep the conversation going\n"
                        "After checking an order, try:\n\n"
                        "“I need it for class. What should I do now?”\n\n"
                        "You don't need to repeat the order number.")
    gr.Markdown("Practice with historical records. This app can suggest help, "
                "but cannot change orders or issue refunds.")

    # Enter and Send do the same job. Reset uses the same queue to avoid stale replies.
    gr.on(triggers=[message.submit, send.click], fn=reply,
          inputs=[message, history], outputs=[message, chat, history, order_card],
          concurrency_id="conversation", api_name="reply")
    gr.on(triggers=[clear.click, chat.clear], fn=reset_chat,
          outputs=[message, chat, history, order_card],
          concurrency_id="conversation", api_name="reset")


if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"), server_port=7860,
        theme=gr.themes.Soft(primary_hue="teal", neutral_hue="slate"),
        css=".gradio-container {max-width: 1100px !important;} "
            "#eyebrow {letter-spacing: .12em; font-size: 12px; color: #0f766e;}",
        footer_links=[], share=False,
    )
