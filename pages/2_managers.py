import streamlit as st
from database import DatabaseManager
from components import display_manager_list

st.title("マネージャー一覧")

try:
    # Initialize database
    db = DatabaseManager()
    
    # Get all managers data
    managers_df = db.get_all_managers()
    
    # Display manager list
    if managers_df.empty:
        st.warning("マネージャーデータが見つかりません")
    else:
        st.info("マネージャー名をクリックすると詳細を確認できます")
        display_manager_list(managers_df)
        
except Exception as e:
    st.error(f"マネージャー一覧の表示中にエラーが発生しました: {str(e)}")
