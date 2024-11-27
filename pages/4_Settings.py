import streamlit as st
import os
from database import get_database_session
from models import AIModelConfig, CacheConfig
from sqlalchemy.sql import select
import logging

def init_settings():
    if "settings_initialized" not in st.session_state:
        st.session_state.settings_initialized = True
        st.session_state.ai_model_settings = {}
        st.session_state.cache_settings = {}

def load_settings():
    db = get_database_session()
    try:
        # AIモデル設定の読み込み
        ai_model_config = db.execute(select(AIModelConfig)).first()
        if ai_model_config:
            st.session_state.ai_model_settings = ai_model_config[0].__dict__

        # キャッシュ設定の読み込み
        cache_config = db.execute(select(CacheConfig)).first()
        if cache_config:
            st.session_state.cache_settings = cache_config[0].__dict__
    except Exception as e:
        logging.error(f"設定の読み込み中にエラーが発生しました: {str(e)}")
    finally:
        db.close()

def save_settings(settings_type, settings_data):
    db = get_database_session()
    try:
        if settings_type == "ai_model":
            config = AIModelConfig(**settings_data)
            db.merge(config)
        elif settings_type == "cache":
            config = CacheConfig(**settings_data)
            db.merge(config)
        db.commit()
        st.success(f"{settings_type}の設定が保存されました。")
    except Exception as e:
        db.rollback()
        st.error(f"設定の保存中にエラーが発生しました: {str(e)}")
    finally:
        db.close()

def render_ai_model_settings():
    st.subheader("AIモデル設定")
    
    model_name = st.selectbox(
        "使用するAIモデル",
        ["gpt-4", "gpt-3.5-turbo"],
        index=0 if st.session_state.ai_model_settings.get("model_name") == "gpt-4" else 1
    )
    
    temperature = st.slider(
        "温度 (創造性のレベル)",
        min_value=0.0,
        max_value=2.0,
        value=float(st.session_state.ai_model_settings.get("temperature", 0.7)),
        step=0.1
    )
    
    max_tokens = st.number_input(
        "最大トークン数",
        min_value=100,
        max_value=4000,
        value=int(st.session_state.ai_model_settings.get("max_tokens", 2000))
    )
    
    if st.button("AIモデル設定を保存"):
        settings_data = {
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        save_settings("ai_model", settings_data)

def render_cache_settings():
    st.subheader("キャッシュ設定")
    
    cache_enabled = st.toggle(
        "キャッシュを有効にする",
        value=bool(st.session_state.cache_settings.get("enabled", True))
    )
    
    cache_ttl = st.number_input(
        "キャッシュ保持時間（分）",
        min_value=1,
        max_value=1440,
        value=int(st.session_state.cache_settings.get("ttl_minutes", 60))
    )
    
    max_cache_size = st.number_input(
        "最大キャッシュサイズ（MB）",
        min_value=1,
        max_value=1000,
        value=int(st.session_state.cache_settings.get("max_size_mb", 100))
    )
    
    if st.button("キャッシュ設定を保存"):
        settings_data = {
            "enabled": cache_enabled,
            "ttl_minutes": cache_ttl,
            "max_size_mb": max_cache_size
        }
        save_settings("cache", settings_data)

def main():
    st.title("システム設定")
    
    init_settings()
    load_settings()
    
    tab1, tab2 = st.tabs(["AIモデル設定", "キャッシュ設定"])
    
    with tab1:
        render_ai_model_settings()
    
    with tab2:
        render_cache_settings()

if __name__ == "__main__":
    main()
