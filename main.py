import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

# Add the project's root directory to the Python path
# This allows for absolute imports from the 'backend' package
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

try:
    # Use absolute imports from the backend package
    from backend.finance_service import get_financial_data, calculate_expected_return, get_ticker_info
    from backend.news_service import get_financial_news, summarize_news_for_llm
    from backend.llm_service import get_llm_response
except ImportError as e:
    st.error(f"Error importing backend services: {e}. Please ensure the backend files exist in a 'backend' folder at the project root.")
    st.stop()


# --- Page Configuration ---
st.set_page_config(
    page_title="Monexa - Your AI Financial Advisor",
    page_icon="🤖",
    layout="wide"
)

# --- Pre-defined Ticker Lists based on Risk ---
# Provides a starting point for analysis and ensures charts have data
RISK_TICKERS = {
    "Low": ["VOO", "BND", "JEPI", "MSFT", "JPM"],
    "Medium": ["VTI", "VXUS", "SCHD", "AAPL", "GOOGL"],
    "High": ["QQQ", "ARKK", "TSLA", "BTC-USD", "ETH-USD"]
}

# --- UI Rendering ---
# Main header with columns for better layout
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://em-content.zobj.net/source/microsoft-teams/363/robot_1f916.png", width=120)
with col2:
    st.title("Monexa AI Financial Advisor")
    st.markdown("Your personalized guide to smart investing. Let's build a plan for your financial future!")

# --- Sidebar for User Inputs ---
with st.sidebar:
    st.header("👤 Your Financial Profile")

    goal = st.selectbox(
        "What is your primary financial goal?",
        ("Investing", "Saving", "Getting a Loan"),
        help="Select the main objective you want to achieve."
    )

    user_inputs = {"goal": goal}

    if goal == "Investing" or goal == "Saving":
        user_inputs["savings"] = st.number_input(
            "How much can you save monthly ($)?",
            min_value=0, step=50, value=500,
            help="Enter the amount you can comfortably set aside each month."
        )
        user_inputs["horizon"] = st.slider(
            "What is your time horizon?",
            min_value=1, max_value=30, value=10, format="%d years",
            help="How many years are you planning to save or invest for?"
        )
        user_inputs["risk"] = st.select_slider(
            "What is your risk tolerance?",
            options=["Low", "Medium", "High"], value="Medium",
            help="Low risk aims for stable, modest returns. High risk has potential for higher growth but also higher volatility."
        )
    
    if goal == "Investing":
        custom_tickers_input = st.text_area(
            "Track specific tickers (optional):",
            placeholder="e.g., GOOGL, BTC-USD, AMZN",
            help="Enter any stock or crypto tickers you want to include in the analysis, separated by commas."
        )
        user_inputs["tickers"] = [ticker.strip().upper() for ticker in custom_tickers_input.split(',') if ticker.strip()]

    analyze_button = st.button("✨ Get My Personalized Advice", use_container_width=True, type="primary")

# --- Helper function to display results ---
def display_results(user_inputs):
    """Encapsulates the logic to fetch data, generate insights, and render UI elements."""
    try:
        # 1. Fetch Backend Data
        financial_news = get_financial_news()
        news_context = summarize_news_for_llm(financial_news)

        # 2. Determine tickers to analyze and validate them
        tickers_to_chart = RISK_TICKERS.get(user_inputs.get("risk", "Medium"), [])
        if user_inputs.get("tickers"):
            valid_custom_tickers = [t for t in user_inputs["tickers"] if get_ticker_info(t) is not None]
            invalid_tickers = set(user_inputs["tickers"]) - set(valid_custom_tickers)
            if invalid_tickers:
                st.warning(f"Could not find data for these tickers: {', '.join(invalid_tickers)}. They will be ignored.")
            tickers_to_chart.extend(valid_custom_tickers)
            tickers_to_chart = list(set(tickers_to_chart))

        # 3. Create context for the LLM
        financial_data_context = ""
        if tickers_to_chart:
            # Create a simple context string for the LLM
            returns = {t: f"{calculate_expected_return(get_financial_data([t])):.2f}%" for t in tickers_to_chart[:5]}
            financial_data_context = f"Expected annual returns for some relevant tickers are: {returns}"

        # 4. Get LLM Response
        llm_response = get_llm_response(user_inputs, financial_data_context, news_context)

        # 5. Display AI Summary in a styled container
        st.subheader("💡 Your AI-Generated Plan")
        with st.container(border=True):
            st.markdown(llm_response)

        # 6. Visualization (only for Investing goal)
        if goal == "Investing" and tickers_to_chart:
            st.subheader("📊 Visualizing Your Potential")
            with st.container(border=True):
                hist_data = get_financial_data(tickers_to_chart, period="5y")
                
                if hist_data is None or hist_data.empty:
                    st.warning("Could not fetch historical data for visualization.")
                    return

                tab1, tab2 = st.tabs(["📈 Growth Simulation", "📊 Expected Returns"])

                with tab1:
                    # --- Chart 1: Animated Growth of $10,000 ---
                    st.markdown("##### Growth of a $10,000 Investment Over 5 Years")
                    st.markdown("This animated chart shows how a one-time $10,000 investment could have grown over the past five years based on historical performance.")

                    # Normalize data for growth comparison
                    df_normalized = pd.DataFrame()
                    for ticker in tickers_to_chart:
                        if (ticker, 'Adj Close') in hist_data.columns:
                            adj_close = hist_data[(ticker, 'Adj Close')].dropna()
                            if not adj_close.empty:
                                df_normalized[ticker] = (adj_close / adj_close.iloc[0]) * 10000
                    
                    if not df_normalized.empty:
                        df_normalized.reset_index(inplace=True)
                        df_melted = df_normalized.melt(id_vars=['Date'], var_name='Ticker', value_name='Portfolio Value')
                        
                        # Set a dynamic but sensible y-axis range
                        min_val, max_val = df_melted['Portfolio Value'].min(), df_melted['Portfolio Value'].max()
                        padding = (max_val - min_val) * 0.1
                        
                        fig_growth = px.line(
                            df_melted, x="Date", y="Portfolio Value", color='Ticker',
                            labels={"Portfolio Value": "Portfolio Value ($)", "Ticker": "Assets"},
                            animation_frame="Date", animation_group="Ticker",
                            range_y=[min_val - padding, max_val + padding],
                            template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Plotly
                        )
                        fig_growth.update_layout(legend_title_text='Assets')
                        st.plotly_chart(fig_growth, use_container_width=True)

                with tab2:
                    # --- Chart 2: Bar Chart of Expected Returns ---
                    st.markdown("##### Comparison of Expected Annual Returns")
                    st.markdown("This chart compares the average annualized return of each asset, calculated from its performance over the last year.")
                    returns_data = {ticker: calculate_expected_return(hist_data[ticker].dropna()) for ticker in tickers_to_chart if ticker in hist_data}
                    
                    if returns_data:
                        returns_df = pd.DataFrame(list(returns_data.items()), columns=["Ticker", "Return"]).sort_values("Return", ascending=False)
                        
                        fig_returns = px.bar(
                            returns_df, x="Ticker", y="Return", color="Return",
                            title="Annualized Return Expectation", template="plotly_dark",
                            labels={"Return": "Expected Annual Return (%)"},
                            color_continuous_scale=px.colors.sequential.Tealgrn,
                            text_auto='.2f'
                        )
                        fig_returns.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
                        st.plotly_chart(fig_returns, use_container_width=True)

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.error("Please check your API keys in the .env file, your internet connection, and try again.")


# --- Main Content Area ---
if analyze_button:
    # Validate inputs before proceeding
    if goal == "Investing" and not user_inputs.get("risk"):
        st.error("Please select a risk tolerance for investing.")
    else:
        # Use a spinner to show that the app is working
        with st.spinner("Monexa AI is crafting your personalized plan..."):
            display_results(user_inputs)
else:
    # Initial welcome message
    st.info("Please fill out your profile in the sidebar to get started!")
    st.markdown("### How it works:")
    st.markdown("1. **Tell us your goal:** Are you investing for growth, saving for a big purchase, or need a loan?")
    st.markdown("2. **Set your parameters:** Define your monthly savings, time horizon, and risk comfort level.")
    st.markdown("3. **Get Instant Insights:** Our AI analyzes market data and news to give you a personalized summary, recommendations, and interactive charts to visualize your financial journey.")

# --- Disclaimer ---
st.markdown("---")
st.markdown("*Disclaimer: Monexa AI provides information and suggestions based on financial data and AI models. This is not financial advice. Please consult with a qualified financial professional before making any investment decisions.*")

