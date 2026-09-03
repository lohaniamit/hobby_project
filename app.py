"""Demo screen for the diagnostic agent.

Holds the layout only. The notebook builds the agent and passes its answer function in,
so nothing here is a second copy of anything.
"""

import gradio as gr
import pandas as pd

colours = {"grounded": "#1a7f37", "needs review": "#9a6700", "blocked": "#b42318"}
meaning = {"grounded": "evidence checks out",
           "needs review": "a person should look at this",
           "blocked": "citations could not be verified"}


def badge(state, why):
    reasons = "".join(f"<li>{w}</li>" for w in why)
    return (f"<div style='padding:10px 14px;border-radius:8px;color:white;"
            f"background:{colours.get(state, '#555')}'>"
            f"<b>{state.upper()}</b> &mdash; {meaning.get(state, '')}"
            f"<ul style='margin:6px 0 0 16px;font-size:0.9em'>{reasons}</ul></div>")


def written_out(reply, out):
    if isinstance(reply, str):
        return "Nothing was looked up for this one."
    lines = [f"**Confidence** {reply.overall_confidence} &nbsp;&nbsp; "
             f"**tools used** {len(out['calls'])} &nbsp;&nbsp; **attempts** {out['attempts']}", ""]
    lines.append("**What was looked up**")
    for name, args, rows in out["calls"]:
        shown = ", ".join(f"{k}={v}" for k, v in args.items())
        lines.append(f"- `{name}({shown})` &rarr; {rows} rows")
    lines += ["", "**Relationships walked**", ", ".join(f"`{p}`" for p in reply.evidence_paths) or "none"]
    lines += ["", "**Evidence cited**"]
    for d in reply.likely_causes_or_drivers:
        lines.append(f"- {d.item} &mdash; {', '.join(f'`{i}`' for i in d.evidence_ids) or 'no ids'}")
    if reply.contradictory_or_missing_evidence:
        lines += ["", "**Missing or contradictory**"]
        lines += [f"- {x}" for x in reply.contradictory_or_missing_evidence]
    if reply.risk_or_governance_flags:
        lines += ["", "**Flags**"] + [f"- {x}" for x in reply.risk_or_governance_flags]
    return "\n".join(lines)


def spoken(reply):
    if isinstance(reply, str):
        return reply
    out = [reply.diagnosis, ""]
    if reply.likely_causes_or_drivers:
        out.append("**Why**")
        out += [f"- {d.item}" for d in reply.likely_causes_or_drivers]
    if reply.recommended_next_actions:
        out += ["", "**What to do**"]
        out += [f"- {a}" for a in reply.recommended_next_actions]
    return "\n".join(out)


def build(answer, before_after=None):
    with gr.Blocks(title="Demand-to-Delivery Diagnostic Agent") as demo:
        gr.Markdown("## Demand-to-Delivery Diagnostic Agent\n"
                    "Ask why a product, plant or part is at risk. Every answer is checked "
                    "against the evidence it was given before it reaches you.")
        thread = gr.State([])

        with gr.Row():
            with gr.Column(scale=3):
                # gradio 6 dropped the type argument; messages is the only format now
                chat = gr.Chatbot(height=440, show_label=False)
                box = gr.Textbox(placeholder="Why is the grain flow sensor short at Prairie Junction?",
                                 show_label=False, submit_btn=True)
                gr.Examples(label="Try one",
                            examples=["Why is Part SC-417 projected to create a shortage at Plant P2?",
                                      "Are there approved substitutes for SC-417 and what constraints apply?",
                                      "Why is BR-1055 at risk at Cedar Falls?",
                                      "Why is the grain flow sensor short?",
                                      "What is the weather in Dallas?"],
                            inputs=box)
            with gr.Column(scale=2):
                state = gr.HTML(badge("grounded", ["nothing asked yet"]))
                detail = gr.Markdown("Evidence appears here once you ask something.")

        if before_after is not None:
            with gr.Accordion("Before and after tuning", open=False):
                gr.Dataframe(before_after, interactive=False)

        def respond(question, chat_so_far, history):
            if not question.strip():
                return chat_so_far, history, badge("grounded", ["nothing asked yet"]), ""
            out = answer(question, history)
            chat_so_far = chat_so_far + [{"role": "user", "content": question},
                                         {"role": "assistant", "content": spoken(out["reply"])}]
            return (chat_so_far, out.get("history", history),
                    badge(out["state"], out["why"]), written_out(out["reply"], out))

        box.submit(respond, [box, chat, thread], [chat, thread, state, detail]).then(
            lambda: "", None, box)

    return demo
