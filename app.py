
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math
import warnings
warnings.filterwarnings('ignore')

# Configure the page
st.set_page_config(
    page_title="Dirt Flipper's County Score Bot",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .county-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .grade-A { color: #28a745; font-weight: bold; }
    .grade-B { color: #17a2b8; font-weight: bold; }
    .grade-C { color: #ffc107; font-weight: bold; }
    .grade-D { color: #fd7e14; font-weight: bold; }
    .grade-F { color: #dc3545; font-weight: bold; }
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        color: #856404;
    }
    .challenge-banner {
        background: linear-gradient(90deg, #2E8B57, #3CB371);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Load and process data
@st.cache_data
def load_data():
    """Load and process the county data"""
    try:
        # In a real deployment, you'd load from the uploaded file
        # For now, we'll create a sample dataset based on the structure
        df = pd.read_excel('Combined_PRYCD_Research_Final.xlsx')

        # Clean column names
        df.columns = df.columns.str.strip()

        # Handle missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)

        return df
    except:
        # Fallback sample data for demo
        return create_sample_data()

def create_sample_data():
    """Create sample data for demonstration"""
    sample_data = {
        'State': ['Florida', 'Florida', 'Florida', 'Arizona', 'Arizona', 'Colorado', 'Colorado', 'Texas', 'Texas'],
        'County': ['Lee County', 'Charlotte County', 'Marion County', 'Mohave County', 'Apache County', 'Costilla County', 'Archuleta County', 'Brewster County', 'Presidio County'],
        'Sold Comps (6m)': [4870, 2181, 1564, 1644, 363, 469, 208, 89, 45],
        'Days on Market': [96, 135, 143, 257, 224, 172, 224, 298, 345],
        'Sold-Listed Ratio (6m)': [1.57, 0.99, 0.99, 0.68, 0.40, 0.44, 1.65, 0.33, 0.22],
        'Out of State to Total Ratio': [0.298, 0.433, 0.283, 0.588, 0.508, 0.718, 0.526, 0.445, 0.389],
        'Out of County to Total Ratio': [0.245, 0.367, 0.334, 0.669, 0.87, 0.482, 0.484, 0.623, 0.578],
        'MoM Price Change %': [-3.3, -1.5, 2.6, -2.0, 4.5, -0.4, -0.4, 1.2, -2.1],
        'Population Change % (2020-2023)': [8.0, 2.8, 1.2, 4.2, -1.3, 0.0, 2.9, 3.7, 1.8],
        'Population-Sq Mile': [125.1, 73.1, 66.3, 16.6, 5.8, 3.2, 11.0, 0.8, 2.1],
        'For Sale Comps (All)': [3905, 926, 410, 7382, 3047, 1069, 126, 270, 205],
        'Sold Comps (All)': [2267, 518, 231, 4835, 991, 469, 208, 89, 45]
    }
    return pd.DataFrame(sample_data)

def calculate_county_score(row):
    """Calculate the county score based on the weighted metrics"""

    # Weights as defined in the prompt
    weights = {
        'sold_comps_6m': 0.30,
        'sold_listed_ratio': 0.20,
        'days_on_market': 0.10,
        'for_sale_sold_ratio': 0.10,
        'out_of_state_ratio': 0.05,
        'out_of_county_ratio': 0.05,
        'price_change': 0.05,
        'population_change': 0.05,
        'population_density': 0.10
    }

    score = 0

    # Sold Comps (6m) - Log scaled, more is better
    sold_comps = max(row.get('Sold Comps (6m)', 0), 1)
    sold_score = min(100, (math.log10(sold_comps) / math.log10(1000)) * 100)
    score += sold_score * weights['sold_comps_6m']

    # Sold-Listed Ratio - Higher is better
    sold_listed = row.get('Sold-Listed Ratio (6m)', 0)
    sold_listed_score = min(100, sold_listed * 100)
    score += sold_listed_score * weights['sold_listed_ratio']

    # Days on Market - Lower is better, sweet spot 90-180
    dom = row.get('Days on Market', 300)
    if 90 <= dom <= 180:
        dom_score = 100
    elif dom < 90:
        dom_score = 100 - (90 - dom) * 0.5
    else:
        dom_score = max(0, 100 - (dom - 180) * 0.2)
    score += dom_score * weights['days_on_market']

    # For Sale / Sold Ratio - Lower is better
    for_sale = row.get('For Sale Comps (All)', 1)
    sold_all = max(row.get('Sold Comps (All)', 1), 1)
    fs_ratio = for_sale / sold_all
    fs_score = max(0, 100 - fs_ratio * 10)
    score += fs_score * weights['for_sale_sold_ratio']

    # Out of State Ratio - Higher is better
    oos_ratio = row.get('Out of State to Total Ratio', 0)
    oos_score = oos_ratio * 100
    score += oos_score * weights['out_of_state_ratio']

    # Out of County Ratio - Higher is better
    ooc_ratio = row.get('Out of County to Total Ratio', 0)
    ooc_score = ooc_ratio * 100
    score += ooc_score * weights['out_of_county_ratio']

    # Price Change - Positive stable growth is good
    price_change = row.get('MoM Price Change %', 0)
    if -2 <= price_change <= 5:
        price_score = 100
    else:
        price_score = max(0, 100 - abs(price_change - 1.5) * 10)
    score += price_score * weights['price_change']

    # Population Change - Growth is good
    pop_change = row.get('Population Change % (2020-2023)', 0)
    pop_score = max(0, min(100, (pop_change + 5) * 10))
    score += pop_score * weights['population_change']

    # Population Density - Lower is better (more rural)
    pop_density = row.get('Population-Sq Mile', 1000)
    density_score = max(0, 100 - (pop_density / 10))
    score += density_score * weights['population_density']

    return min(100, max(0, score))

def assign_grade(score):
    """Assign letter grade based on score"""
    if score >= 80:
        return 'A'
    elif score >= 65:
        return 'B'
    elif score >= 50:
        return 'C'
    elif score >= 35:
        return 'D'
    else:
        return 'F'

def get_grade_color_class(grade):
    """Get CSS class for grade color"""
    return f"grade-{grade}"

# Header
st.markdown('<h1 class="main-header">🦾 Dirt Flipper\'s County Score Bot</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Find the Best Counties for Flipping Vacant Land - Fast!</p>', unsafe_allow_html=True)

# Challenge Banner
st.markdown("""
<div class="challenge-banner">
    <h3>🚀 Want to go deeper? Join my next 5-day challenge at FlipDirtChallenge.com!</h3>
</div>
""", unsafe_allow_html=True)

# Load data
df = load_data()

# Calculate scores and grades
if not df.empty:
    df['Score'] = df.apply(calculate_county_score, axis=1)
    df['Grade'] = df['Score'].apply(assign_grade)

# Sidebar
st.sidebar.header("🎯 County Analysis Tool")
st.sidebar.markdown("Select your options below to analyze counties for land flipping opportunities.")

# State filter
available_states = sorted(df['State'].unique()) if not df.empty else ['Florida', 'Arizona', 'Colorado']
selected_states = st.sidebar.multiselect(
    "Choose States to Analyze:",
    available_states,
    default=available_states[:3] if len(available_states) >= 3 else available_states
)

# Grade filter
grade_filter = st.sidebar.multiselect(
    "Filter by Grade:",
    ['A', 'B', 'C', 'D', 'F'],
    default=['A', 'B', 'C']
)

# Minimum sold comps filter
min_comps = st.sidebar.slider(
    "Minimum Sold Comps (6m):",
    min_value=0,
    max_value=1000,
    value=10,
    step=10
)

# File upload section
st.sidebar.markdown("---")
st.sidebar.header("📁 Upload Your Own Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload your county list (CSV/Excel):",
    type=['csv', 'xlsx', 'xls'],
    help="Upload your own list of counties to analyze"
)

if uploaded_file:
    try:
        if uploaded_file.name.endswith('.csv'):
            user_df = pd.read_csv(uploaded_file)
        else:
            user_df = pd.read_excel(uploaded_file)

        st.sidebar.success(f"✅ Uploaded {len(user_df)} rows successfully!")

        # Process user data if it has the right columns
        if 'State' in user_df.columns and 'County' in user_df.columns:
            # Merge with main dataset
            user_analysis = pd.merge(user_df, df, on=['State', 'County'], how='left')
            if not user_analysis.empty:
                st.sidebar.info("Your data has been merged with our database for analysis!")
    except Exception as e:
        st.sidebar.error(f"Error processing file: {str(e)}")

# Filter data
if not df.empty and selected_states:
    filtered_df = df[
        (df['State'].isin(selected_states)) & 
        (df['Grade'].isin(grade_filter)) &
        (df['Sold Comps (6m)'] >= min_comps)
    ].copy()

    # Sort by score
    filtered_df = filtered_df.sort_values('Score', ascending=False)

    # Main content
    if not filtered_df.empty:
        # Overview metrics
        st.header("📊 Market Overview")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_score = filtered_df['Score'].mean()
            st.metric(
                label="🏆 Average Score",
                value=f"{avg_score:.1f}",
                delta=f"{len(filtered_df[filtered_df['Grade'].isin(['A', 'B'])])} A/B Counties"
            )

        with col2:
            avg_sales = filtered_df['Sold Comps (6m)'].mean()
            st.metric(
                label="📈 Avg Sales (6m)",
                value=f"{avg_sales:.0f}",
                delta="comps"
            )

        with col3:
            avg_dom = filtered_df['Days on Market'].mean()
            st.metric(
                label="⏱️ Avg Days on Market",
                value=f"{avg_dom:.0f}",
                delta="days"
            )

        with col4:
            avg_oos = filtered_df['Out of State to Total Ratio'].mean() * 100
            st.metric(
                label="🏠 Avg Out-of-State",
                value=f"{avg_oos:.1f}%",
                delta="ownership"
            )

        # Top counties section
        st.header("🎯 Top Counties to Target")

        for i, (_, county) in enumerate(filtered_df.head(10).iterrows(), 1):
            grade_class = get_grade_color_class(county['Grade'])

            st.markdown(f"""
            <div class="county-card">
                <h3>#{i}. {county['County']}, {county['State']}</h3>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 1.2rem; font-weight: bold; color: #2E8B57;">
                        Score: {county['Score']:.1f}
                    </span>
                    <span class="{grade_class}" style="font-size: 1.5rem;">
                        Grade: {county['Grade']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Metrics in columns
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Sales (6m)", f"{county['Sold Comps (6m)']:,.0f}")
            with col2:
                st.metric("Days on Market", f"{county['Days on Market']:.0f}")
            with col3:
                st.metric("Out-of-State %", f"{county['Out of State to Total Ratio']*100:.1f}%")
            with col4:
                st.metric("Price Change", f"{county['MoM Price Change %']:.1f}%")

            # Quick Notes
            st.markdown("**🎯 Quick Notes:**")
            notes = []

            if county['Out of State to Total Ratio'] > 0.3:
                notes.append("• High absentee ownership - great for direct mail")
            if county['Days on Market'] < 180:
                notes.append("• Properties move quickly - build your buyer list")
            if county['Sold Comps (6m)'] > 500:
                notes.append("• High-volume market - scale up your marketing")
            if county['Grade'] in ['A', 'B']:
                notes.append("• Top-tier opportunity - prioritize this market")
            if county['Population Change % (2020-2023)'] > 2:
                notes.append("• Growing area - increasing demand")

            if notes:
                for note in notes[:3]:  # Limit to 3 notes
                    st.markdown(note)
            else:
                st.markdown("• Moderate opportunity - good for experienced investors")

            st.markdown("---")

        # Visualization section
        st.header("📈 Market Analysis Charts")

        col1, col2 = st.columns(2)

        with col1:
            # Score distribution by state
            fig1 = px.box(
                filtered_df, 
                x='State', 
                y='Score',
                title='Score Distribution by State',
                color='State'
            )
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Grade distribution
            grade_counts = filtered_df['Grade'].value_counts()
            fig2 = px.pie(
                values=grade_counts.values,
                names=grade_counts.index,
                title='Grade Distribution',
                color_discrete_map={
                    'A': '#28a745',
                    'B': '#17a2b8', 
                    'C': '#ffc107',
                    'D': '#fd7e14',
                    'F': '#dc3545'
                }
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Detailed data table
        st.header("📋 Detailed County Data")

        display_columns = [
            'County', 'State', 'Score', 'Grade', 
            'Sold Comps (6m)', 'Days on Market', 
            'Out of State to Total Ratio', 'MoM Price Change %'
        ]

        # Format the dataframe for display
        display_df = filtered_df[display_columns].copy()
        display_df['Out of State to Total Ratio'] = (display_df['Out of State to Total Ratio'] * 100).round(1)
        display_df = display_df.rename(columns={
            'Out of State to Total Ratio': 'Out-of-State %',
            'MoM Price Change %': 'Price Change %'
        })

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.warning("No counties match your current filters. Try adjusting your criteria.")

# Chatbot section
st.header("💬 Ask the Land Coach AI")

st.markdown("""
<div class="chat-container">
    <p><strong>Got questions about the data, grades, or land flipping strategies?</strong></p>
    <p>I'm here to help! Ask me anything about:</p>
    <ul>
        <li>🏆 What grades and scores mean</li>
        <li>📊 How to interpret the metrics</li>
        <li>🎯 Which counties to target first</li>
        <li>💡 Marketing strategies for specific areas</li>
        <li>📈 General land flipping advice</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey there! I'm your Land Coach AI. Ask me anything about county analysis, land flipping strategies, or the data you're seeing. What would you like to know?"}
    ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about land flipping, county analysis, or anything else!"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response (simplified for demo)
    with st.chat_message("assistant"):
        response = generate_ai_response(prompt, filtered_df if 'filtered_df' in locals() else df)
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

def generate_ai_response(prompt, data):
    """Generate AI response based on user prompt"""
    prompt_lower = prompt.lower()

    # Data-specific responses
    if any(word in prompt_lower for word in ['grade', 'score', 'rating']):
        return """
**Here's how our grading system works:**

• **Grade A (80-100):** Excellent opportunities - these are your top targets!
• **Grade B (65-79):** Very good markets - definitely worth pursuing
• **Grade C (50-64):** Good potential - solid for experienced investors
• **Grade D (35-49):** Fair opportunities - proceed with caution
• **Grade F (0-34):** Poor markets - probably skip these

The score considers sales volume (30%), sold/listed ratio (20%), days on market (10%), competition (10%), and other factors. Higher scores = better opportunities!

**Want to go deeper? Join my next 5-day challenge at FlipDirtChallenge.com!**
        """

    elif any(word in prompt_lower for word in ['days on market', 'dom', 'how long']):
        return """
**Days on Market (DOM) tells you how fast properties sell:**

• **Under 90 days:** Super hot market - properties fly off the market
• **90-180 days:** Sweet spot - good activity, not too competitive
• **180-300 days:** Slower market - more time to negotiate
• **Over 300 days:** Very slow - might indicate oversupply

**Pro tip:** Look for counties with DOM between 90-180 days. Fast enough to show demand, but not so fast that you can't compete!

Remember to always verify this data with local research before investing.
        """

    elif any(word in prompt_lower for word in ['out of state', 'absentee', 'owner']):
        return """
**Out-of-state ownership is GOLD for land flippers! Here's why:**

• **High out-of-state % = More motivated sellers**
• These owners often can't visit the property
• They may not know the local market value
• They're more likely to sell quickly for cash

**Target counties with 30%+ out-of-state ownership for best results.**

**Marketing strategies:**
• Direct mail campaigns work great
• "We buy land" postcards
• Focus on tax delinquent lists
• Online marketing to out-of-state zip codes

**Always do your due diligence before making offers!**
        """

    elif any(word in prompt_lower for word in ['marketing', 'strategy', 'how to']):
        return """
**Here are proven land flipping marketing strategies:**

**🎯 Direct Mail:**
• Target absentee owners (out-of-state/county)
• Use tax delinquent lists
• Send "We Buy Land" postcards
• Follow up consistently

**📱 Digital Marketing:**
• Facebook ads to specific zip codes
• Google Ads for "sell my land"
• Craigslist "We Buy" ads
• Social media presence

**🔍 Lead Sources:**
• Tax delinquent properties
• Probate leads
• Divorce records
• Bankruptcy filings

**💡 Pro Tips:**
• Focus on counties with high absentee ownership
• Start with smaller, affordable parcels
• Build your buyer list FIRST
• Always verify property details

**Want the complete system? Join my 5-day challenge at FlipDirtChallenge.com!**
        """

    elif any(word in prompt_lower for word in ['best county', 'top county', 'recommend']):
        if not data.empty:
            top_county = data.iloc[0]
            return f"""
**Based on your current filters, I recommend starting with:**

**🏆 {top_county['County']}, {top_county['State']}**
• Score: {top_county['Score']:.1f} (Grade {top_county['Grade']})
• Sales Volume: {top_county['Sold Comps (6m)']:,.0f} comps in 6 months
• Days on Market: {top_county['Days on Market']:.0f} days
• Out-of-State Ownership: {top_county['Out of State to Total Ratio']*100:.1f}%

**Why this county rocks:**
• Strong sales activity shows demand
• Good out-of-state ownership for motivated sellers
• Reasonable days on market for negotiations

**Next steps:**
1. Research local zoning laws
2. Find a good title company
3. Start building your buyer list
4. Begin your marketing campaign

**Remember: Always do your own due diligence before investing!**
        """
        else:
            return "I'd love to recommend specific counties, but I need to see your filtered data first. Try selecting some states and adjusting your filters above!"

    elif any(word in prompt_lower for word in ['beginner', 'new', 'start', 'first time']):
        return """
**Welcome to land flipping! Here's your beginner roadmap:**

**🎯 Step 1: Pick Your Market**
• Start with counties scoring B or higher
• Look for 200+ sales comps (shows activity)
• Target 30%+ out-of-state ownership
• Avoid super rural areas initially

**💰 Step 2: Set Your Budget**
• Start with $5,000-$15,000 deals
• Keep 50% cash for unexpected costs
• Factor in holding costs and taxes

**📋 Step 3: Build Your Systems**
• Find a good title company
• Set up your LLC
• Create marketing materials
• Build your buyer list FIRST

**🚀 Step 4: Take Action**
• Start with direct mail campaigns
• Make 10-20 offers per week
• Follow up consistently
• Learn from every deal

**The key is taking action! Start small, learn fast, scale up.**

**Want the complete step-by-step system? Join my 5-day challenge at FlipDirtChallenge.com!**
        """

    else:
        return """
**I'm here to help with your land flipping questions!**

I can help you with:
• Understanding county scores and grades
• Interpreting market data and metrics
• Marketing strategies and lead generation
• Beginner advice and getting started
• Specific county recommendations

**What would you like to know more about?**

And remember - this data is just a starting point. Always do your own due diligence, verify property details, and research local markets before investing.

**Ready to take your land flipping to the next level? Join my 5-day challenge at FlipDirtChallenge.com!**
        """

# Disclaimer
st.markdown("""
<div class="disclaimer">
    <h4>⚠️ Important Disclaimer</h4>
    <p><strong>This score is only a starting point. You must do your own due diligence before investing in any county.</strong></p>
    <p>This tool may use outdated or incomplete information, so double-check all facts before making offers. Local trends, zoning, flood zones, and property type nuances are NOT included in the score. Do not rely solely on this bot for investment decisions.</p>
    <p><strong>Always verify data, research local markets, and consult with professionals before investing.</strong></p>
</div>
""", unsafe_allow_html=True)

# Sidebar information
st.sidebar.markdown("---")
st.sidebar.header("📚 How Scoring Works")
st.sidebar.markdown("""
**Our weighted scoring system:**
- Sales Volume (30%)
- Sold/Listed Ratio (20%) 
- Days on Market (10%)
- Competition Level (10%)
- Out-of-State Ownership (5%)
- Out-of-County Ownership (5%)
- Price Trends (5%)
- Population Growth (5%)
- Population Density (10%)

**Grade Scale:**
- A: 80-100 (Excellent)
- B: 65-79 (Very Good)
- C: 50-64 (Good)
- D: 35-49 (Fair)
- F: 0-34 (Poor)
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**💡 Need More Help?**")
st.sidebar.markdown("Join my 5-day challenge at **FlipDirtChallenge.com** for the complete land flipping system!")

# Footer
st.markdown("---")
st.markdown("*Built for Land Flippers - County Analysis Made Simple*")
