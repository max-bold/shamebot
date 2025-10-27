import streamlit as st
from database import Session, engine, select, User

# import db_handlers as dbh

st.title("Shamebot Administration Panel")


params = st.query_params
admin_id = params.get("admin")
st.text(f"Admin ID1: {admin_id}")

with Session(engine) as session:
    for user in session.exec(select(User)).all():
        st.text(f"User ID: {user.id}, Username: @{user.user_name}")
