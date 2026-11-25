from __future__ import annotations

from pathlib import Path

import streamlit as st

from showcase_data import ROOT


_STYLE_PATH = Path(__file__).resolve().parent / "assets" / "style.css"


def apply_shared_style() -> None:
    if not _STYLE_PATH.is_file():
        raise FileNotFoundError(f"Showcase stylesheet is missing: {_STYLE_PATH}")
    st.markdown(
        f"<style>{_STYLE_PATH.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, *, eyebrow: str) -> None:
    st.markdown(
        f"""
        <div class="page-header">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <section class="showcase-panel metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-note">{note}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def show_source_reference(relative_path: str) -> None:
    path = (ROOT / relative_path).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        st.error(f"Source reference unavailable: {relative_path}")
        return
    st.caption(f"Source: `{relative_path}`")
