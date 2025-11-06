import streamlit as st

def page_1():
    st.title("Page 1")

def page_2():
    st.title("Page 2")

pg = st.navigation([page_1, page_2], position="top")
pg.run()