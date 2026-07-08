from io import BytesIO
import requests
import streamlit as st
from huggingface_hub import InferenceClient

import config

MODEL_ID = "stabilityai/stable-diffusion-3-medium-diffusers"
FILTER_API_URL = "https://filters-zeta.vercel.app/api/filter"

ENHANCE_SYS = (
    "Improve prompts for text-to-image. Return ONLY the enhanced prompt. "
    "Add subject, style, lighting, camera angle, background, colors. Keep it safe."
)

NEGATIVE = "low quality, blurry, bad anatomy, disfigured, deformed, mutated, ugly, poorly drawn, distorted, extra limbs, missing limbs, cropped, worst quality, distorted, watermark, text, cropped"

img_client = InferenceClient(provider="hf-inference", api_key=config.HF_API_KEY)


def check_prompt_with_filter_api(prompt: str):
    try:
        response = requests.post(FILTER_API_URL, json={"prompt": prompt}, timeout=10)
        response.raise_for_status()
        result = response.json()

        if not isinstance(result, dict):
            return {"ok": False, "reason": "Invalid response format from filter API."}
        return result
    except Exception as e:
        return {"ok": False, "reason": f"Filter API error: {e}"}
    

def enhance_prompt(raw: str) -> str:
    from hf import generate_response

    out = generate_response(ENHANCE_SYS + "\n\n" + raw, temperature=0.4, max_tokens=1024)
    return (out or raw).strip()


def gen_image(prompt: str):
    filter_result = check_prompt_with_filter_api(prompt)
    if not filter_result.get("ok"):
        return None, f"Prompt rejected by filter API: {filter_result.get('reason', 'Unknown reason')}"
    
    try:
        return img_client.text_to_image(
            prompt=prompt,
            negative_prompt=NEGATIVE,
            model=MODEL_ID,
        ), None
    except Exception as e:
        msg = str(e)

        if "negative_prompt" in msg.lower() or "unexpected" in msg.lower():
            try:
                return img_client.text_to_image(
                    prompt=prompt,
                    model=MODEL_ID,
                ), None
            except Exception as e2:
                msg = str(e2)
        
        if any(x in msg for x in ["402", "Payment Required", "pre-paid credits"]):
            return None, "❌ Image backend requires credits or model not available on hf-inference.\n\nRaw error: " + msg

        if "404" in msg or "Not Found" in msg:
            return None, "❌ Model not served on this provider route (hf-inference).\n\nRaw error: " + msg

        return None, "Error during image generation: " + msg
    
def main():
    st.set_page_config(page_title="Safe AI Image Generator", layout="centered")
    st.title("🖼️ Safe AI Image Generator")
    st.info("Flow: Enter a prompt → enhance it → check it using the deployed safety API → generate the image.")

    with st.form("image_form"):
        raw = st.text_area(
            "Image Description",
            height=120,
            placeholder="Example: A cozy cabin in snowy mountains at sunrise, cinematic lighting",
        )
        submit = st.form_submit_button("Generate Image")

    if submit:
        raw = raw.strip()
        if not raw:
            st.warning("Please enter a prompt before clicking 'Generate Image'.")
            return
        
        raw_check = check_prompt_with_filter_api(raw)
        if not raw_check.get("ok"):
            st.error(f"❌ Prompt rejected by filter API: {raw_check.get('reason', 'Unknown reason')}")
            return
        
        with st.spinner("Enhancing prompt..."):
            enhanced = enhance_prompt(raw)

        enhanced_check = check_prompt_with_filter_api(enhanced)
        if not enhanced_check.get("ok"):
            st.error(f"❌ Enhanced prompt rejected by filter API: {enhanced_check.get('reason', 'Unknown reason')}")
            return
        
        st.markdown("Enhanced Prompt")
        st.code(enhanced)

        with st.spinner("Generating Image..."):
            img, err = gen_image(enhanced)
        
        if err:
            st.error(err)
            return
        
        st.image(img, caption="Generate Image", use_container_width=True)
        st.session_state.generate_image = img

    img = st.session_state.get("generated_image")
    if img:
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.download_button(
            "📥 Download Image",
            buf.getvalue(),
            "ai_generated_image.png",
            "image/png",
        )

if __name__ == "__main__":
    main()