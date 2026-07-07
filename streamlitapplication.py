from hf import generate_response
# from groq import generate_response

import io, streamlit as st

SYSTEM_PROMPT = """You are a Math Mastermind. For every math problem:
1) Show step-by-step solution  2) Explain reasoning  3) Give alternate method if possible
4) Verify answer if possible  5) Use proper notation  6) Break complex problems into parts
Format: Problem → Steps → **Final Answer** → Concepts used. Be precise and educational."""

def math_generate(problem: str, level: str, temperature = 0.1, max_tokens = 1024) -> str:
    prompt = f"{SYSTEM_PROMPT}\n\nLevel: {level}\nProblem: {problem}"
    return generate_response(prompt, temperature=temperature, max_tokens=max_tokens)

def export_txt(history):
    text = "\n\n".join([f"Problem: {h['problem']}\nLevel: {h['level']}\nSolution: {h['solution']}\n\n" for h in history])
    return io.BytesIO(text.encode("utf-8"))

def setup_ui():
    st.set_page_config(page_title="Math Mastermind", layout="centered")
    st.title("🧮 Math Mastermind")
    st.write("Solve math problems step-by-step with detailed explanations and alternate methods.")

    with st.expander("Examples"):
        st.markdown(
            """
            - **Algebra**: Solve for x: 2x + 3 = 11
            - **Calculus**: Differentiate f(x) = x^3 + 2x^2 - 5x + 7
            - **Geometry**: Find the area of a triangle with base 5 and height 10
            - **Probability**: What is the probability of rolling a sum of 7 with two dice?
            - **Number Theory**: Find the greatest common divisor (GCD) of 48 and 180
            """
        )
    
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("k", 0)

    c1, c2 = st.columns([1, 2])
    if c1.button("Clear History"):
        st.session_state.history = []
        st.rerun()

    if st.session_state.history:
        c2.download_button("Export", export_txt(st.session_state.history), file_name="math_history.txt", mime="text/plain")

    with st.form("math_form", clear_on_submit=True):
        q = st.text_area("Enter your math problem:", height=100, placeholder="Type your math problem here...", key=f"q{st.session_state.k}")
        a, b = st.columns([3, 1])
        solve = a.form_submit_button("Solve", use_container_width=True)
        level = b.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"], index=1)

        if solve:
            if not q.strip(): st.warning("Please enter a math problem before clicking 'Solve'."); st.stop()
            else:
                with st.spinner("Solving..."):
                    solution = math_generate(q.strip(), level)
                st.session_state.history.append({"problem": q.strip(), "level": level, "solution": solution})
                st.session_state.k += 1
                st.rerun()
    if not st.session_state.history: return
    st.markdown("### History of Solved Problems")
    st.markdown("""<style>
    .box{max-height:500px;overflow-y:auto;border:2px solid #4CAF50;padding:12px;background:#f7fbff;border-radius:10px}
    .q{font-weight:700;color:#2E7D32;margin-top:12px}
    .lvl{display:inline-block;background:#FF9800;color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;margin-left:8px}
    .a{white-space:pre-wrap;color:#1B5E20;background:#fff;padding:10px;border-radius:8px;border-left:4px solid #4CAF50;margin:6px 0 14px}
    </style>""", unsafe_allow_html=True)

    html = '<div class="box">'
    for i, h in enumerate(st.session_state.history, 1):
        html += f'<div class="q">Q{i}: {h["problem"]}<span class="lvl">{h["level"]}</span></div>'
        html += f'<div class="a">{h["solution"]}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    setup_ui()