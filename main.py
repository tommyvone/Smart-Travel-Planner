
import streamlit as st
import openai
import requests
import googlemaps
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any

def check_api_status(planner):
    """Check which APIs are configured"""
    status = {
        'openai': planner.openai_client is not None,
        'weather': planner.weather_api_key is not None,
        'google_maps': planner.gmaps is not None
    }
    return status

def display_api_status(status):
    """Display API configuration status"""
    st.markdown("### 🔧 API Configuration Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if status['openai']:
            st.success("✅ OpenAI API Ready")
        else:
            st.error("❌ OpenAI API Missing")
            
    with col2:
        if status['weather']:
            st.success("✅ Weather API Ready")
        else:
            st.error("❌ Weather API Missing")
            
    with col3:
        if status['google_maps']:
            st.success("✅ Google Maps Ready")
        else:
            st.warning("⚠️ Google Maps Optional")
    
    if not all([status['openai'], status['weather']]):
        st.info("💡 **Need API Keys?** Click the '+ Secrets' button to add your API keys and unlock all features!")

# Set page configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class TravelPlanner:
    def __init__(self):
        self.openai_client = None
        self.gmaps = None
        self.weather_api_key = None
        self.setup_apis()
    
    def setup_apis(self):
        """Initialize API clients"""
        try:
            # Check for API keys in Streamlit secrets or environment variables
            openai_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
            google_maps_key = st.secrets.get("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
            self.weather_api_key = st.secrets.get("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHER_API_KEY")
            
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
            if google_maps_key:
                self.gmaps = googlemaps.Client(key=google_maps_key)
                
        except Exception as e:
            st.error(f"Error setting up APIs: {e}")
    
    def get_destination_suggestions(self, budget: str, interests: List[str], climate: str, departure_city: str) -> str:
        """Get travel destination suggestions using OpenAI"""
        if not self.openai_client:
            return "OpenAI API not configured. Please add your API key."
        
        try:
            location_info = departure_city
            if hasattr(st.session_state, 'zip_code') and st.session_state.get('zip_code'):
                location_info = f"{departure_city} (Zip: {st.session_state.zip_code})"
            
            prompt = f"""
            Suggest 3-5 travel destinations based on the following preferences:
            - Budget: {budget}
            - Interests: {', '.join(interests)}
            - Preferred climate: {climate}
            - Departing from: {location_info}
            
            For each destination, provide:
            1. Destination name and country
            2. Why it matches their preferences
            3. Estimated budget breakdown
            4. Best time to visit
            
            Format as a clear, readable list.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting destination suggestions: {e}"
    
    def get_weather_forecast(self, city: str) -> Dict[str, Any]:
        """Get weather forecast for a destination"""
        if not self.weather_api_key:
            return {"error": "Weather API not configured"}
        
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.weather_api_key,
                "units": "metric"
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return {
                    "temperature": data["main"]["temp"],
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "feels_like": data["main"]["feels_like"]
                }
            else:
                return {"error": "City not found"}
        except Exception as e:
            return {"error": f"Weather API error: {e}"}
    
    def generate_itinerary(self, destination: str, interests: List[str], days: int) -> str:
        """Generate daily itinerary using OpenAI"""
        if not self.openai_client:
            return "OpenAI API not configured."
        
        try:
            prompt = f"""
            Create a detailed {days}-day itinerary for {destination} based on these interests: {', '.join(interests)}.
            
            For each day, include:
            - Morning activity
            - Afternoon activity
            - Evening activity
            - Recommended restaurants
            - Transportation tips
            
            Format as Day 1, Day 2, etc. with clear sections.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating itinerary: {e}"
    
    def generate_packing_list(self, destination: str, weather: Dict[str, Any], days: int) -> str:
        """Generate packing list based on destination and weather"""
        if not self.openai_client:
            return "OpenAI API not configured."
        
        try:
            weather_info = f"Temperature: {weather.get('temperature', 'N/A')}°C, {weather.get('description', 'N/A')}"
            
            prompt = f"""
            Create a comprehensive packing list for a {days}-day trip to {destination}.
            Weather conditions: {weather_info}
            
            Include sections for:
            - Clothing
            - Electronics
            - Personal items
            - Travel documents
            - Optional items
            
            Tailor recommendations to the weather and destination.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating packing list: {e}"
    
    def get_visa_info(self, destination: str, nationality: str) -> str:
        """Get visa requirements information"""
        if not self.openai_client:
            return "OpenAI API not configured."
        
        try:
            prompt = f"""
            Provide visa requirement information for a {nationality} citizen traveling to {destination}.
            Include:
            - Visa requirement status (visa-free, visa on arrival, e-visa, or embassy visa required)
            - Duration of stay allowed
            - Required documents
            - Processing time (if applicable)
            - Approximate cost (if applicable)
            
            Note: This is general information and travelers should verify with official sources.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error getting visa information: {e}"

def main():
    st.title("🌍 AI Travel Planner")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;'>
        <h2 style='color: white; margin: 0;'>✈️ Plan Your Perfect Adventure!</h2>
        <p style='color: white; margin: 5px 0 0 0;'>AI-powered travel recommendations tailored just for you</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize the travel planner
    planner = TravelPlanner()
    
    # Check API status
    api_status = check_api_status(planner)
    display_api_status(api_status)
    
    # Sidebar for user inputs
    st.sidebar.header("✈️ Your Travel Preferences")
    st.sidebar.markdown("Fill in your details below to get personalized recommendations!")
    
    # User input collection with better organization
    st.sidebar.markdown("#### 📍 Location Details")
    departure_city = st.sidebar.text_input("🏠 Departure City", "New York", help="Where will you be traveling from?")
    
    zip_code = st.sidebar.text_input(
        "📮 Your Zip Code (Optional)", 
        placeholder="e.g. 10001",
        help="💡 Adding your zip code helps us provide more accurate local recommendations and travel times!"
    )
    
    nationality = st.sidebar.text_input("🌍 Your Nationality", "American", help="Needed for visa requirements")
    
    st.sidebar.markdown("#### 💰 Budget & Dates")
    budget = st.sidebar.selectbox(
        "💵 Budget Range",
        ["Budget ($0-$1000)", "Mid-range ($1000-$3000)", "Luxury ($3000+)"],
        help="Choose your comfortable spending range"
    )
    
    travel_dates = st.sidebar.date_input(
        "📅 Travel Dates",
        value=(datetime.now().date(), datetime.now().date() + timedelta(days=7)),
        help="Select your trip start and end dates"
    )
    
    st.sidebar.markdown("#### 🎯 Preferences")
    interests = st.sidebar.multiselect(
        "🎪 What interests you?",
        ["🏖️ Beaches", "🏛️ Museums", "🥾 Hiking", "🍕 Food", "🌃 Nightlife", "📚 History", "🛍️ Shopping", "🏄 Adventure Sports", "🐾 Wildlife", "🏗️ Architecture"],
        default=["🏖️ Beaches", "🍕 Food"],
        help="Select all that apply - the more you choose, the better our recommendations!"
    )
    
    climate = st.sidebar.selectbox(
        "🌡️ Preferred Climate",
        ["☀️ Warm", "❄️ Cool", "🌴 Tropical", "🌤️ Temperate", "🤷 No preference"],
        help="What weather makes you happiest?"
    )
    
    # Calculate trip duration
    if len(travel_dates) == 2:
        trip_days = (travel_dates[1] - travel_dates[0]).days
    else:
        trip_days = 7
    
    # Main interface tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Destinations", "🌤️ Weather", "📅 Itinerary", "🎒 Packing", "📋 Visa Info"])
    
    # Add some spacing and styling
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Ready to Explore?")
    
    # Check if minimum requirements are met
    can_plan = departure_city and interests
    
    if not can_plan:
        st.sidebar.warning("⚠️ Please fill in your departure city and interests first!")
    
    plan_button = st.sidebar.button(
        "🚀 Plan My Amazing Trip!", 
        type="primary", 
        disabled=not can_plan,
        help="Click to generate your personalized travel plan!"
    )
    
    if plan_button:
        # Store zip code in session state
        if zip_code:
            st.session_state['zip_code'] = zip_code
            
        st.balloons()  # Celebratory animation!
        
        with st.spinner("🌟 Creating your perfect adventure..."):
            
            # Tab 1: Destination Suggestions
            with tab1:
                st.header("🎯 Recommended Destinations")
                destinations = planner.get_destination_suggestions(budget, interests, climate, departure_city)
                st.write(destinations)
                
                # Store destination for other tabs
                st.session_state['destinations'] = destinations
            
            # Tab 2: Weather Information
            with tab2:
                st.header("🌤️ Weather Forecast")
                st.markdown("Check current weather conditions for your chosen destination")
                
                # Simple destination input for weather
                destination_for_weather = st.text_input(
                    "🏙️ Enter destination city for weather:",
                    placeholder="e.g. Paris, Tokyo, New York",
                    help="💡 Enter a city name from the recommended destinations above"
                )
                
                if destination_for_weather:
                    with st.spinner(f"Getting weather for {destination_for_weather}..."):
                        weather = planner.get_weather_forecast(destination_for_weather)
                        if "error" not in weather:
                            st.success(f"Weather data found for {destination_for_weather}!")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("🌡️ Temperature", f"{weather['temperature']}°C")
                            with col2:
                                st.metric("🤚 Feels Like", f"{weather['feels_like']}°C")
                            with col3:
                                st.metric("💧 Humidity", f"{weather['humidity']}%")
                            with col4:
                                st.metric("☁️ Conditions", weather['description'].title())
                            
                            # Weather recommendation
                            temp = weather['temperature']
                            if temp > 25:
                                st.info("🌞 Perfect weather for outdoor activities!")
                            elif temp > 15:
                                st.info("🌤️ Great weather! Pack a light jacket for evenings.")
                            else:
                                st.info("🧥 Cool weather - don't forget warm clothes!")
                            
                            st.session_state['weather'] = weather
                            st.session_state['destination_city'] = destination_for_weather
                        else:
                            st.error(f"❌ {weather['error']} - Please try a different city name")
            
            # Tab 3: Itinerary
            with tab3:
                st.header("📅 Daily Itinerary")
                destination_for_itinerary = st.text_input(
                    "Enter destination for itinerary:",
                    value=st.session_state.get('destination_city', ''),
                    help="Enter the destination city"
                )
                
                if destination_for_itinerary:
                    itinerary = planner.generate_itinerary(destination_for_itinerary, interests, trip_days)
                    st.write(itinerary)
            
            # Tab 4: Packing List
            with tab4:
                st.header("🎒 Packing List")
                if 'weather' in st.session_state and 'destination_city' in st.session_state:
                    packing_list = planner.generate_packing_list(
                        st.session_state['destination_city'], 
                        st.session_state['weather'], 
                        trip_days
                    )
                    st.write(packing_list)
                else:
                    st.info("Please check weather information first to generate a tailored packing list.")
            
            # Tab 5: Visa Information
            with tab5:
                st.header("📋 Visa Requirements")
                destination_for_visa = st.text_input(
                    "Enter destination country for visa info:",
                    help="Enter the country name"
                )
                
                if destination_for_visa and nationality:
                    visa_info = planner.get_visa_info(destination_for_visa, nationality)
                    st.write(visa_info)
                    st.warning("⚠️ This is general information. Please verify with official embassy sources before traveling.")
    
    # API Configuration Help
    with st.expander("🔧 Need Help Setting Up API Keys?"):
        st.markdown("""
        ### 🎯 Quick Setup Guide
        
        **Step 1: Get Your Free API Keys**
        - 🤖 **OpenAI** → [Get API Key](https://platform.openai.com/api-keys) (Required for AI features)
        - 🌤️ **OpenWeatherMap** → [Get Free Key](https://openweathermap.org/api) (Required for weather)
        - 🗺️ **Google Maps** → [Get API Key](https://developers.google.com/maps/documentation/javascript/get-api-key) (Optional)
        
        **Step 2: Add to Replit Secrets**
        1. Click the **+ button** in any pane and type "Secrets"
        2. Add these three secrets:
           - **Key:** `OPENAI_API_KEY` **Value:** [Your OpenAI key]
           - **Key:** `OPENWEATHER_API_KEY` **Value:** [Your weather key]
           - **Key:** `GOOGLE_MAPS_API_KEY` **Value:** [Your maps key]
        
        **Step 3: Restart the app** (click the Run button again)
        
        ✨ **Pro Tip:** OpenWeatherMap offers a generous free tier - perfect for testing!
        """)
        
        if not all([planner.openai_client, planner.weather_api_key]):
            st.warning("⚠️ Add your API keys above to unlock all the amazing features!")

if __name__ == "__main__":
    main()
