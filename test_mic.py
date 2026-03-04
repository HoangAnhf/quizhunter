import streamlit as st
from streamlit_mic_recorder import mic_recorder, speech_to_text

st.set_page_config(page_title="Test Microphone", page_icon="🎤")
st.title("🎤 Test Microphone")

st.markdown("---")
st.subheader("Test 1: mic_recorder")
st.caption("Bấm nút bên dưới để ghi âm. Trình duyệt sẽ hỏi quyền mic - bấm Allow.")

audio = mic_recorder(
    start_prompt="🎤 Bắt đầu ghi âm",
    stop_prompt="⏹️ Dừng ghi âm",
    just_once=False,
    use_container_width=True,
    format="webm",
    key="test_mic_1",
)

if audio:
    st.write("Audio data received!")
    st.write(f"Type: {type(audio)}")
    st.write(f"Keys: {audio.keys() if isinstance(audio, dict) else 'not a dict'}")
    if isinstance(audio, dict) and audio.get("bytes"):
        st.write(f"Audio size: {len(audio['bytes'])} bytes")
        st.audio(audio["bytes"], format="audio/webm")
    else:
        st.write(f"Raw value: {audio}")
else:
    st.info("Chưa có audio. Bấm nút ghi âm ở trên.")

st.markdown("---")
st.subheader("Test 2: speech_to_text (built-in Google STT)")
st.caption("Test speech_to_text - dùng Google Speech Recognition miễn phí.")

text = speech_to_text(
    start_prompt="🎤 Ghi âm + Nhận dạng",
    stop_prompt="⏹️ Dừng",
    just_once=False,
    use_container_width=True,
    language="vi-VN",
    key="test_stt_1",
)

if text:
    st.success(f"Nhận dạng được: **{text}**")
else:
    st.info("Chưa có text. Bấm nút ghi âm ở trên.")
