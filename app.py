"""Interactive Streamlit Showcase for LLM Engineering Portfolio.

Features interactive playgrounds for:
1. Semantic Cache (FAISS vector search, similarity thresholding, negation guards, PII filters).
2. LLM-as-a-Judge Audit (Position bias, length bias, bidirectional debiased evaluation).
3. RAG Prompt Injection (10 adversarial attack scenarios, 4 layered defenses).
"""

import os
import sys
import json
import streamlit as st

# Setup paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "p1-semantic-cache"))
sys.path.insert(0, os.path.join(ROOT_DIR, "p2-llm-judge"))
sys.path.insert(0, os.path.join(ROOT_DIR, "p3-rag-injection"))

# Import project modules
from cache import SemanticCache
from bot import FAQBot
from judge import judge_pair, load_rubric
from rag import RAGBot
from attack_runner import check_attack_success

st.set_page_config(
    page_title="LLM Engineering Portfolio | Shivam Jaiswal",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Production LLM Systems & Evaluation Portfolio")
st.markdown(
    "**Author:** Shivam Jaiswal | **GitHub:** [Shivam9621/llm-portfolio](https://github.com/Shivam9621/llm-portfolio)\n\n"
    "Three end-to-end LLM engineering projects with real empirical benchmarks and interactive evaluation environments."
)

tab1, tab2, tab3 = st.tabs([
    "⚡ Project 1: Semantic Cache",
    "⚖️ Project 2: LLM Judge Audit",
    "🛡️ Project 3: Prompt Injection Defense",
])

# =============================================================================
# TAB 1: SEMANTIC CACHE
# =============================================================================
with tab1:
    st.header("⚡ Project 1: Semantic Cache for an FAQ Bot")
    st.info(
        "**Verified Metric:** Cache hit rate **14.0%** on 100 test questions at threshold **0.75** "
        "with **0 false hits**; LLM calls down **14.0%**; average latency down from **1144 ms to 986 ms**."
    )

    col1, col2 = st.columns([2, 1])

    with col2:
        st.subheader("⚙️ Cache Settings")
        threshold = st.slider("Cosine Similarity Threshold", min_value=0.50, max_value=0.95, value=0.75, step=0.05)
        enable_neg_guard = st.checkbox("Enable Negation Guard", value=True, help="Blocks polarity mismatches (e.g. 'not return')")
        enable_pii_filter = st.checkbox("Enable PII / Order ID Filter", value=True, help="Refuses caching sensitive tokens")

    with col1:
        st.subheader("💬 Query Playground")
        preset = st.selectbox(
            "Select a preset query or type your own below:",
            [
                "Custom Query",
                "What is your return policy? (Exact Match)",
                "How do I contact customer support representatives? (Semantic Hit)",
                "Please do not give me any refund, keep the payment (Adversarial Negation)",
                "Where can I buy Bitcoin? (Out of Scope)",
            ],
        )

        default_text = ""
        if "Exact" in preset:
            default_text = "What is your return policy?"
        elif "Semantic" in preset:
            default_text = "How do I contact customer support representatives?"
        elif "Negation" in preset:
            default_text = "Please do not give me any refund, keep the payment"
        elif "Out of Scope" in preset:
            default_text = "Where can I buy Bitcoin?"

        query_input = st.text_input("Customer Inquiry:", value=default_text)

        if st.button("Submit to FAQ Bot", key="p1_submit"):
            if query_input.strip():
                faq_path = os.path.join(ROOT_DIR, "p1-semantic-cache", "faqs.json")
                cache = SemanticCache(
                    threshold=threshold,
                    enable_negation_guard=enable_neg_guard,
                    enable_pii_filter=enable_pii_filter,
                )
                bot = FAQBot(cache=cache, faq_file=faq_path, default_threshold=threshold)
                res = bot.ask(query_input, threshold=threshold)

                if res["hit"]:
                    st.success(f"🎯 **[CACHE HIT]** (Matched: `{res['matched_faq_id']}` | Similarity: `{res['similarity']:.4f}`)")
                else:
                    neg_blocked = res.get("audit", {}).get("negation_blocked", False)
                    if neg_blocked:
                        st.warning(f"🛡️ **[LLM FALLBACK - NEGATION GUARD ACTIVATED]** (Similarity: `{res['similarity']:.4f}`)")
                    else:
                        st.warning(f"⚡ **[CACHE MISS - LLM GENERATION]** (Similarity: `{res['similarity']:.4f}` < Threshold)")

                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Latency", f"{res['latency_ms']:.2f} ms", delta="-98.2% vs LLM" if res["hit"] else None)
                col_m2.metric("Tokens Consumed", f"{res['tokens_in'] + res['tokens_out']}", delta="0 tokens" if res["hit"] else None)
                col_m3.metric("Source", res["source"].upper())

                st.markdown(f"**Bot Answer:**\n> {res['answer']}")

# =============================================================================
# TAB 2: LLM JUDGE AUDIT
# =============================================================================
with tab2:
    st.header("⚖️ Project 2: LLM-as-a-Judge Audit & Debiasing")
    st.info(
        "**Verified Metric:** Judge agreed with human on **8/30 (26.7%)**; swapping order changed **25 verdicts**; "
        "judging in both orders with length-neutrality raised agreement to **11/30 (36.7%)**."
    )

    questions_path = os.path.join(ROOT_DIR, "p2-llm-judge", "questions.json")
    answers_path = os.path.join(ROOT_DIR, "p2-llm-judge", "answers.jsonl")

    with open(questions_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)

    with open(answers_path, "r", encoding="utf-8") as f:
        answers_dict = {row["id"]: row for row in [json.loads(line) for line in f]}

    selected_qid = st.selectbox(
        "Select an Engineering Question to Judge:",
        options=[q["id"] for q in questions_data],
        format_func=lambda qid: f"{qid}: {next(q['question'] for q in questions_data if q['id'] == qid)[:80]}...",
    )

    chosen_pair = answers_dict[selected_qid]

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Model A: Concise Senior Engineer")
        st.caption(f"Word count: {len(chosen_pair['answer_a'].split())} words")
        st.markdown(chosen_pair["answer_a"])

    with col_b:
        st.subheader("Model B: Verbose Academic")
        st.caption(f"Word count: {len(chosen_pair['answer_b'].split())} words")
        st.markdown(chosen_pair["answer_b"])

    st.markdown("---")
    st.subheader("⚖️ Judge Configuration")
    col_j1, col_j2 = st.columns(2)
    with col_j1:
        swap_order = st.checkbox("Swap Presentation Order (Present Model B then Model A)", value=False)
    with col_j2:
        length_neutral = st.checkbox("Inject 'Length Does Not Matter' Instruction", value=False)

    if st.button("Evaluate with LLM Judge", key="p2_judge"):
        verdict = judge_pair(
            question=chosen_pair["question"],
            answer_a=chosen_pair["answer_a"],
            answer_b=chosen_pair["answer_b"],
            swap_order=swap_order,
            length_penalty_instruction=length_neutral,
        )

        winner_label = verdict["winner"]
        if winner_label == "A":
            st.success(f"🏆 Winner: **Model A (Concise Engineer)** | Reason: {verdict['reason']}")
        elif winner_label == "B":
            st.info(f"🏆 Winner: **Model B (Verbose Academic)** | Reason: {verdict['reason']}")
        else:
            st.warning(f"🤝 Outcome: **TIE** | Reason: {verdict['reason']}")

        st.caption(f"Presentation: {verdict['presentation']} | Raw Choice: Candidate {verdict['raw_choice']}")

# =============================================================================
# TAB 3: PROMPT INJECTION DEFENSE
# =============================================================================
with tab3:
    st.header("🛡️ Project 3: Indirect Prompt-Injection Attack & Defense Sandbox")
    st.info(
        "**Verified Metric:** Successful injections: **10/10 before**, **0/10 after guardrails**; "
        "**0 false blocks on 20 normal questions**."
    )

    attacks_file = os.path.join(ROOT_DIR, "p3-rag-injection", "attacks.json")
    with open(attacks_file, "r", encoding="utf-8") as f:
        attacks_data = json.load(f)

    col_atk, col_def = st.columns([2, 1])

    with col_def:
        st.subheader("🛡️ Defense Layers (Defense in Depth)")
        l1 = st.checkbox("Layer 1: Spotlighting (<document> tags + passive rule)", value=True)
        l2 = st.checkbox("Layer 2: Input Filter (Chunk quarantining)", value=True)
        l3 = st.checkbox("Layer 3: Output Filter (Regex leak redaction)", value=True)
        l4 = st.checkbox("Layer 4: Least Privilege (Secret removal)", value=True)

    with col_atk:
        st.subheader("🎯 Adversarial Vector")
        atk_idx = st.selectbox(
            "Select an Injection Attack Scenario:",
            range(len(attacks_data)),
            format_func=lambda i: f"Attack #{i+1}: {attacks_data[i]['name']}",
        )
        selected_atk = attacks_data[atk_idx]
        st.markdown(f"**Trigger Query:** `{selected_atk['trigger_query']}`")
        st.markdown(f"**Target Pattern:** `{selected_atk['target_pattern']}`")
        st.caption(f"Technique: {selected_atk['description']}")

        if st.button("Launch RAG Query", key="p3_launch"):
            bot = RAGBot(
                layer_spotlighting=l1,
                layer_input_filter=l2,
                layer_output_filter=l3,
                layer_least_privilege=l4,
            )
            res = bot.query(selected_atk["trigger_query"])
            is_success = check_attack_success(res["response"], selected_atk["condition_type"], selected_atk["target_pattern"])

            st.markdown("---")
            if is_success:
                st.error(f"🚨 **[PWNED - ATTACK SUCCEEDED: SECRET '{selected_atk['target_pattern']}' LEAKED]**")
            else:
                st.success("✅ **[DEFENDED - SECRET SECURE & ATTACK NEUTRALIZED]**")

            st.markdown(f"**Bot Response:**\n> {res['response']}")
            st.caption(f"Retrieved Files: {res['audit']['retrieved_files']} | Poison in Top-3: {res['audit']['retrieved_poison']}")
