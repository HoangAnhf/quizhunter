import streamlit as st


def render_search_bar(placeholder: str = "Nhập chủ đề hoặc nội dung cần tìm...") -> str | None:
    default_val = st.session_state.get("search_query", "")
    with st.form(key="search_form"):
        col1, col2 = st.columns([5, 1])
        with col1:
            query = st.text_input("Tìm kiếm", value=default_val, placeholder=placeholder, label_visibility="collapsed")
        with col2:
            submit = st.form_submit_button("🔍 Tìm kiếm", use_container_width=True)

    if submit and query.strip():
        return query.strip()
    return None