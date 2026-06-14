import streamlit as st

import styles
import views


st.set_page_config(page_title="일단막아 · DEFENSE FIRST", page_icon="🛡️", layout="wide")


def main() -> None:
    styles.inject()

    if "user" not in st.session_state:
        views.login_view()
        return

    user = st.session_state.user
    nav = views.sidebar(user)
    if nav.startswith("🔍"):
        views.new_diagnosis_view(user)
    else:
        views.shared_cases_view(user)


if __name__ == "__main__":
    main()
