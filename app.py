"""The screen: conversation controls on the left, chat on the right."""
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
    history = gr.State([])
    with gr.Row():
        with gr.Column(scale=1, min_width=230, elem_id="sidebar"):
            gr.Markdown("### AlmaBetter\nOrder support", elem_id="brand")
            clear = gr.Button("＋ New chat", elem_id="new-chat")
            order_card = gr.Markdown(EMPTY_ORDER)
            gr.Markdown("---\nHistorical practice records.\n\n"
                        "This app cannot change orders or issue refunds.", elem_id="sidebar-note")
        with gr.Column(scale=4, min_width=300):
            gr.Markdown("# Order support\nAsk about your parcel. We'll help you find the next step.")
            chat = gr.Chatbot(
                label="Conversation", show_label=False, height=430, layout="bubble",
                placeholder="How can we help with your order?",
                render_markdown=False, buttons=["copy"],
            )
            with gr.Row():
                message = gr.Textbox(
                    show_label=False, placeholder="Type your message…",
                    lines=1, max_lines=3, scale=5,
                )
                send = gr.Button("Send", variant="primary", scale=1, min_width=85)
            gr.Examples(
                examples=[["Where is order ee64d42b8cf066f35eac1cf57de1aa85?"]],
                inputs=message, label="Try an example",
            )
            gr.Markdown("You can ask follow-up questions without repeating the order number.")

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
        theme=gr.themes.Base(primary_hue="red", neutral_hue="zinc",
                             font=["Arial", "sans-serif"]),
        css="""
            .gradio-container {max-width: 1180px !important;}
            #sidebar {background: #f5f5f5; border-radius: 12px; padding: 18px; gap: 24px;}
            #sidebar .prose, #sidebar .prose * {color: #525252; font-size: 13px;}
            #sidebar h3 {font-size: 14px !important; color: #171717 !important;}
            #sidebar code {background: #eaeaea; overflow-wrap: anywhere;}
            #sidebar hr {border-color: #e5e5e5;}
            #brand h3 {font-size: 18px !important; letter-spacing: -.03em;}
            #new-chat {background: transparent; border: 0; box-shadow: none;
                       color: #171717; justify-content: flex-start; text-align: left; padding: 10px 12px; border-radius: 8px;}
            #new-chat:hover {background: #e8e8e8;}
            #sidebar-note {margin-top: auto;}
            .dark #sidebar {background: #202020;}
            .dark #sidebar .prose, .dark #sidebar .prose * {color: #bcbcbc;}
            .dark #sidebar h3, .dark #new-chat {color: #f5f5f5 !important;}
            .dark #sidebar code, .dark #new-chat:hover {background: #303030;}
            @media (min-width: 768px) {#sidebar {min-height: 660px;}}
            button.primary {background: #dc2626 !important; color: white !important;}
            button.primary:hover {background: #b91c1c !important;}
        """,
        footer_links=[], share=False,
    )
