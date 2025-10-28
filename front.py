import streamlit as st
import db_handlers as dbh


st.title("Shamebot Administration Panel")


params = st.query_params
admin_id = params.get("admin")

with st.sidebar:
    st.text(f"Admin ID: {admin_id}")
    st.header("Select chat")
    if admin_id:
        for chat in dbh.get_chats_by_admin(int(admin_id)):
            if st.button(f"**{chat.chat_name}**\n\n{chat.id}"):
                st.session_state["selected_chat_id"] = chat.id


@st.dialog("Delete chat", dismissible=False)
def chat_delete_confirmation(chat_id: int):
    st.text("Are you sure you want to delete this chat from the database?")
    if st.button("Yes, Delete Chat", type="primary"):
        if dbh.delete_chat(chat_id):
            st.success("Chat deleted successfully!")
            del st.session_state["selected_chat_id"]
        else:
            st.error("Failed to delete chat.")
        st.rerun()
        st.rerun()
    if st.button("Cancel"):
        st.rerun()


if "selected_chat_id" in st.session_state:
    chat_id = st.session_state["selected_chat_id"]
    chat = dbh.get_chat(chat_id)
    if chat:
        st.header(f"{chat.chat_name}")
        st.text(f"Chat ID: {chat.id}")
        st.checkbox("Setup Complete", value=chat.setup_complete, disabled=True)
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Trigger Settings")
                chat.text_triggers = st.toggle(
                    "Text Triggers", value=chat.text_triggers
                )
                chat.photo_triggers = st.toggle(
                    "Photo Triggers", value=chat.photo_triggers
                )
                chat.video_triggers = st.toggle(
                    "Video Triggers", value=chat.video_triggers
                )
                chat.voice_triggers = st.toggle(
                    "Voice Triggers", value=chat.voice_triggers
                )
                chat.video_note_triggers = st.toggle(
                    "Video Note Triggers", value=chat.video_note_triggers
                )
                chat.join_triggers = st.toggle(
                    "Join Chat Triggers", value=chat.join_triggers
                )
            with col2:
                st.subheader("Notification Settings")
                chat.notify_time = (
                    st.number_input(
                        "Notification Time (hours)",
                        value=chat.notify_time / 3600,
                        min_value=0.0,
                    )
                    * 3600
                )
                chat.notify_max_time = (
                    st.number_input(
                        "Max Notification Time (hours)",
                        value=chat.notify_max_time / 3600,
                        min_value=0.0,
                    )
                    * 3600
                )
                chat.notify_interval = (
                    st.number_input(
                        "Notification Interval (hours)",
                        value=chat.notify_interval / 3600,
                        min_value=0.0,
                    )
                    * 3600
                )
            if st.button("Save Settings"):
                if dbh.save_chat_settings(chat):
                    st.success("Settings updated successfully!")
                else:
                    st.error("Failed to update settings.")

    with st.container(border=True):
        st.subheader("Chat admins")
        admins = dbh.get_chat_admins(st.session_state["selected_chat_id"])
        with st.table():
            st.write("Admin Name (ID) - Is Muted")
            data = []
            for admin, admin_membership in admins:
                data.append(
                    {
                        "Admin Name": f"@{admin.user_name}",
                        "Admin ID": admin.id,
                        "Is Muted": admin_membership.is_muted,
                    }
                )
            edited_df = st.data_editor(
                data,
                disabled=["Admin Name", "Admin ID"],
                column_config={"Admin ID": st.column_config.TextColumn()},
            )
        if st.button("Save Admin Changes"):
            if dbh.save_admin_settings(edited_df, st.session_state["selected_chat_id"]):
                st.success("Admin settings updated successfully!")
            else:
                st.error("Failed to update admin settings.")

    with st.container(border=True):
        st.subheader("Chat members")
        members = dbh.get_chat_members(chat_id)
        data = []
        for member, member_membership in members:
            data.append(
                {
                    "Member Name": f"@{member.user_name}",
                    "Member ID": member.id,
                    "Is Muted": member_membership.is_muted,
                }
            )
        edited_df = st.data_editor(
            data,
            disabled=["Member Name", "Member ID"],
            column_config={"Member ID": st.column_config.TextColumn()},
        )
        if st.button("Save Member Changes"):
            if dbh.save_member_settings(edited_df, chat_id):
                st.success("Member settings updated successfully!")
            else:
                st.error("Failed to update member settings.")

    if st.button("Delete chat from db", type="primary"):
        chat_delete_confirmation(chat_id)
