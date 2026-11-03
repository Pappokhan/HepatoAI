import pandas as pd
import streamlit as st


def render_about(summary: dict, feature_names):
    st.subheader("Model")
    c1, c2, c3 = st.columns(3)
    c1.metric("Best model", summary["name"])
    acc = summary.get("accuracy")
    c2.metric("Reported accuracy", f"{acc:.2%}" if acc is not None else "n/a")
    c3.metric("Features", summary["n_features"])

    if summary["all_models"]:
        st.write("Accuracy of all trained models")
        s = pd.Series(summary["all_models"], name="accuracy").sort_values(ascending=False)
        st.bar_chart(s)

    st.write("Input features")
    st.dataframe(pd.DataFrame({"Feature": feature_names}), hide_index=True)
