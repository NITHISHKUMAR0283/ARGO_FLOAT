import streamlit as st
from groq import Groq
import time
import json
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="Groq AI Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* Header with gradient */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        color: white;
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        background: linear-gradient(45deg, #fff, #f0f8ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-header p {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Chat container with glassmorphism */
    .chat-container {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
        min-height: 500px;
        max-height: 600px;
        overflow-y: auto;
    }
    
    /* Message bubbles with animations */
    .message-bubble {
        margin: 1rem 0;
        animation: fadeInUp 0.5s ease-out;
        max-width: 85%;
        word-wrap: break-word;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .user-bubble {
        margin-left: auto;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 25px 25px 5px 25px;
        box-shadow: 0 5px 15px rgba(79, 172, 254, 0.3);
        position: relative;
    }
    
    .user-bubble::before {
        content: "👤";
        position: absolute;
        top: -10px;
        right: 10px;
        background: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .bot-bubble {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: #333;
        padding: 1rem 1.5rem;
        border-radius: 25px 25px 25px 5px;
        box-shadow: 0 5px 15px rgba(250, 112, 154, 0.3);
        position: relative;
    }
    
    .bot-bubble::before {
        content: "🤖";
        position: absolute;
        top: -10px;
        left: 10px;
        background: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Sidebar enhancement */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* Welcome screen */
    
    
    .welcome-screen h2 {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    
    .welcome-screen p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 0.5rem;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 1rem;
        color: #666;
        font-style: italic;
    }
    
    .typing-dots {
        display: flex;
        gap: 3px;
    }
    
    .typing-dots span {
        width: 6px;
        height: 6px;
        background: #667eea;
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
    .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
        40% { transform: scale(1); opacity: 1; }
    }
    
    /* Stats cards */
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .stats-number {
        font-size: 2rem;
        font-weight: 700;
        display: block;
    }
    
    .stats-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    /* Model selector enhancement */
    .model-card {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 0.8rem;
        margin: 0.5rem 0;
        backdrop-filter: blur(10px);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #667eea;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button enhancements */
    .stButton > button {
        border-radius: 25px;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-top: 2rem;
    }
    
    /* Dark mode toggle */
    .theme-toggle {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 50px;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with enhanced features
if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'api_key' not in st.session_state:
    st.session_state.api_key = "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"

if 'message_count' not in st.session_state:
    st.session_state.message_count = 0

if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.now()

if 'favorite_model' not in st.session_state:
    st.session_state.favorite_model = "llama3-8b-8192"

# Enhanced Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-content">
        <h2>🚀 AI Control Center</h2>
        <p>Customize your AI experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key Section
    st.markdown("### 🔑 API Configuration")
    api_key = st.text_input(
        "Groq API Key", 
        value=st.session_state.api_key,
        type="password",
        help="🔗 Get your free key at console.groq.com"
    )
    st.session_state.api_key = api_key
    
    if api_key:
        st.success("✅ API Key Connected")
    else:
        st.error("❌ API Key Required")
    
    st.markdown("---")
    
    # Model Selection with descriptions
    st.markdown("### 🧠 AI Model Selection")
    
    model_info = {
        "llama3-8b-8192": {
            "name": "🦙 Llama 3 8B",
            "desc": "Fast & Efficient",
            "strength": "⚡ Speed",
            "color": "#4CAF50"
        },
        "llama3-70b-8192": {
            "name": "🦙 Llama 3 70B", 
            "desc": "Most Powerful",
            "strength": "💪 Intelligence",
            "color": "#2196F3"
        },
        "mixtral-8x7b-32768": {
            "name": "🌟 Mixtral 8x7B",
            "desc": "Creative & Diverse",
            "strength": "🎨 Creativity", 
            "color": "#FF9800"
        },
        "gemma-7b-it": {
            "name": "💎 Gemma 7B",
            "desc": "Google's Model",
            "strength": "🎯 Accuracy",
            "color": "#9C27B0"
        }
    }
    
    selected_model = st.selectbox(
        "Choose your AI companion",
        options=list(model_info.keys()),
        format_func=lambda x: f"{model_info[x]['name']} - {model_info[x]['desc']}",
        index=0
    )
    
    # Model info card
    current_model = model_info[selected_model]
    st.markdown(f"""
    <div class="model-card">
        <h4>{current_model['name']}</h4>
        <p><strong>Specialty:</strong> {current_model['desc']}</p>
        <p><strong>Best for:</strong> {current_model['strength']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Advanced Settings
    st.markdown("### ⚙️ Response Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        temperature = st.slider(
            "🌡️ Creativity",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )
    
    with col2:
        max_tokens = st.slider(
            "📏 Length",
            min_value=100,
            max_value=4000,
            value=1000,
            step=100
        )
    
    # System prompt
    st.markdown("### 📝 System Instructions")
    system_prompt = st.text_area(
        "Customize AI behavior",
        value="You are a helpful, friendly, and knowledgeable AI assistant.",
        height=100
    )
    
    st.markdown("---")
    
    # Session Stats
    st.markdown("### 📊 Session Stats")
    
    session_time = datetime.now() - st.session_state.session_start
    hours, remainder = divmod(session_time.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <span class="stats-number">{st.session_state.message_count}</span>
            <span class="stats-label">Messages</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <span class="stats-number">{hours}h {minutes}m</span>
            <span class="stats-label">Session Time</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Action Buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.messages = []
            st.session_state.message_count = 0
            st.rerun()
    
    with col2:
        if st.button("💾 Export Chat"):
            if st.session_state.messages:
                chat_export = {
                    "timestamp": datetime.now().isoformat(),
                    "model": selected_model,
                    "messages": st.session_state.messages,
                    "settings": {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "system_prompt": system_prompt
                    }
                }
                st.download_button(
                    "📥 Download JSON",
                    data=json.dumps(chat_export, indent=2),
                    file_name=f"groq_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

# Main Content Area


# Check API key
if not api_key:
    
    st.stop()

# Initialize Groq client
try:
    client = Groq(api_key=api_key)
except Exception as e:
    st.error(f"❌ Connection failed: {str(e)}")
    st.info("💡 Please check your API key and internet connection")
    st.stop()

# Chat Interface

# Welcome message
if not st.session_state.messages:
    st.markdown("""
    
    """, unsafe_allow_html=True)

# Display chat messages
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        st.markdown(f"""
        <div class="message-bubble user-bubble">
            <strong>You</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-bubble bot-bubble">
            <strong>AI Assistant</strong><br>
            {message["content"]}
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Chat input with enhanced UX
user_input = st.chat_input("💬 Type your message here... (Press Enter to send)", key="enhanced_chat_input")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.message_count += 1
    
    # Show typing indicator
    typing_placeholder = st.empty()
    typing_placeholder.markdown("""
    <div class="typing-indicator">
        <span>🤖 AI is thinking</span>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Prepare messages with system prompt
        messages_with_system = []
        if system_prompt.strip():
            messages_with_system.append({"role": "system", "content": system_prompt})
        messages_with_system.extend(st.session_state.messages)
        
        # API call with enhanced error handling
        start_time = time.time()
        chat_completion = client.chat.completions.create(
            messages=messages_with_system,
            model=selected_model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        response_time = time.time() - start_time
        response = chat_completion.choices[0].message.content
        
        # Clear typing indicator
        typing_placeholder.empty()
        
        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Show success metrics
        st.success(f"✅ Response generated in {response_time:.2f}s using {selected_model}")
        
        st.rerun()
        
    except Exception as e:
        typing_placeholder.empty()
        st.error(f"❌ Error: {str(e)}")
        st.session_state.messages.pop()  # Remove user message on error
        
        if "rate limit" in str(e).lower():
            st.info("⏰ Rate limit reached. Please wait a moment before sending another message.")
        elif "api key" in str(e).lower():
            st.info("🔑 Please check your API key in the sidebar.")

# Enhanced Footer
