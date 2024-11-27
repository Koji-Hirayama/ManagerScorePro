import streamlit as st
from database import DatabaseManager
from models import AIModelConfig, CacheConfig
import logging

def init_settings():
    if "settings_initialized" not in st.session_state:
        st.session_state.settings_initialized = True
        st.session_state.ai_model_settings = {}
        st.session_state.cache_settings = {}

def load_settings():
    try:
        db = DatabaseManager()
        with db.Session() as session:
            # AIモデル設定の読み込み
            ai_model_config = session.query(AIModelConfig).first()
            if ai_model_config:
                st.session_state.ai_model_settings = {
                    'model_name': ai_model_config.model_name,
                    'temperature': ai_model_config.temperature,
                    'max_tokens': ai_model_config.max_tokens
                }

            # キャッシュ設定の読み込み
            cache_config = session.query(CacheConfig).first()
            if cache_config:
                st.session_state.cache_settings = {
                    'enabled': cache_config.enabled,
                    'ttl_minutes': cache_config.ttl_minutes,
                    'max_size_mb': cache_config.max_size_mb
                }
    except Exception as e:
        logging.error(f"設定の読み込み中にエラーが発生しました: {str(e)}")
        st.error("設定の読み込み中にエラーが発生しました。")

def save_settings(settings_type, settings_data):
    try:
        db = DatabaseManager()
        with db.Session() as session:
            if settings_type == "ai_model":
                config = session.query(AIModelConfig).first()
                if not config:
                    config = AIModelConfig()
                    session.add(config)
                config.model_name = settings_data['model_name']
                config.temperature = settings_data['temperature']
                config.max_tokens = settings_data['max_tokens']
            elif settings_type == "cache":
                config = session.query(CacheConfig).first()
                if not config:
                    config = CacheConfig()
                    session.add(config)
                config.enabled = settings_data['enabled']
                config.ttl_minutes = settings_data['ttl_minutes']
                config.max_size_mb = settings_data['max_size_mb']
            
            session.commit()
            st.success(f"{settings_type}の設定が保存されました。")
    except Exception as e:
        logging.error(f"設定の保存中にエラーが発生しました: {str(e)}")
        st.error(f"設定の保存中にエラーが発生しました: {str(e)}")

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
