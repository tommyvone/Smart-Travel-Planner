
import streamlit as st
import openai
import requests
import googlemaps
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any

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
    st.markdown("### Plan your perfect trip with AI-powered recommendations!")
    
    # Welcome message and instructions
    if not any(key in st.session_state for key in ['destinations', 'trip_planned']):
        st.info("👋 Welcome! Fill out your preferences in the sidebar and click '🚀 Plan My Trip' to get started!")
    
    # Initialize the travel planner
    planner = TravelPlanner()
    
    # Sidebar for user inputs with better organization
    st.sidebar.header("✈️ Your Travel Preferences")
    st.sidebar.markdown("*Fill out the information below to get personalized recommendations*")
    
    with st.sidebar.form("travel_preferences"):
        st.subheader("💰 Budget & Location")
        budget = st.selectbox(
            "Budget Range per person",
            ["Budget ($0-$1000)", "Mid-range ($1000-$3000)", "Luxury ($3000+)"],
            help="Select your total budget range for the entire trip"
        )
        
        departure_city = st.text_input(
            "Departure City", 
            "New York",
            help="Where will you be traveling from?"
        )
        
        zip_code = st.text_input(
            "📍 Your Zip Code (Optional)", 
            placeholder="12345",
            help="Enter your zip code for more accurate location-based recommendations"
        )
        
        st.subheader("📅 Travel Details")
        travel_dates = st.date_input(
            "Travel Dates",
            value=(datetime.now().date(), datetime.now().date() + timedelta(days=7)),
            help="When do you want to travel?"
        )
        
        st.subheader("🎯 Preferences")
        interests = st.multiselect(
            "What interests you most?",
            ["Beaches", "Museums", "Hiking", "Food", "Nightlife", "History", 
             "Shopping", "Adventure Sports", "Wildlife", "Architecture", "Culture", "Relaxation"],
            default=["Beaches", "Food"],
            help="Select all that apply - this helps us recommend the perfect destinations!"
        )
        
        climate = st.selectbox(
            "Preferred Climate",
            ["Warm", "Cool", "Tropical", "Temperate", "No preference"],
            help="What weather do you prefer for your trip?"
        )
        
        nationality = st.text_input(
            "Your Nationality", 
            "American",
            help="This helps us provide accurate visa information"
        )
        
        # Submit button
        plan_trip = st.form_submit_button("🚀 Plan My Trip", type="primary", use_container_width=True)
    
    # Calculate trip duration
    if len(travel_dates) == 2:
        trip_days = (travel_dates[1] - travel_dates[0]).days + 1
        st.sidebar.success(f"Trip duration: {trip_days} days")
    else:
        trip_days = 7
    
    # Main content area
    if plan_trip:
        if not interests:
            st.error("⚠️ Please select at least one interest to get personalized recommendations!")
            return
            
        # Store data in session state
        st.session_state['trip_planned'] = True
        st.session_state['budget'] = budget
        st.session_state['departure_city'] = departure_city
        st.session_state['zip_code'] = zip_code
        st.session_state['interests'] = interests
        st.session_state['climate'] = climate
        st.session_state['nationality'] = nationality
        st.session_state['trip_days'] = trip_days
    
    # Show tabs only if trip has been planned
    if st.session_state.get('trip_planned', False):
        # Progress indicator
        st.markdown("---")
        st.markdown("### 🎯 Your Personalized Travel Plan")
        
        # Main interface tabs with better descriptions
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏝️ Destinations", 
            "🌤️ Weather", 
            "📅 Itinerary", 
            "🎒 Packing", 
            "📋 Visa Info"
        ])
        
        # Tab 1: Destination Suggestions
        with tab1:
            st.header("🏝️ Perfect Destinations for You")
            
            if 'destinations' not in st.session_state:
                with st.spinner("🔍 Finding amazing destinations just for you..."):
                    destinations = planner.get_destination_suggestions(
                        st.session_state['budget'], 
                        st.session_state['interests'], 
                        st.session_state['climate'], 
                        st.session_state['departure_city']
                    )
                    st.session_state['destinations'] = destinations
            
            st.write(st.session_state.get('destinations', ''))
            
            if st.session_state.get('destinations'):
                st.success("💡 Tip: Copy a destination name to use in the other tabs!")
        
        # Tab 2: Weather Information
        with tab2:
            st.header("🌤️ Weather Forecast")
            st.markdown("*Check the current weather at your destination*")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                destination_for_weather = st.text_input(
                    "🏙️ Destination City",
                    placeholder="e.g., Paris, Tokyo, Barcelona",
                    help="Enter a city name from your recommended destinations above"
                )
            with col2:
                check_weather = st.button("Check Weather", type="secondary")
            
            if destination_for_weather and (check_weather or st.session_state.get('weather_checked')):
                with st.spinner("🌡️ Getting current weather..."):
                    weather = planner.get_weather_forecast(destination_for_weather)
                    
                if "error" not in weather:
                    st.session_state['weather'] = weather
                    st.session_state['destination_city'] = destination_for_weather
                    st.session_state['weather_checked'] = True
                    
                    # Weather display with better formatting
                    st.subheader(f"Current Weather in {destination_for_weather}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("🌡️ Temperature", f"{weather['temperature']}°C")
                    with col2:
                        st.metric("🤗 Feels Like", f"{weather['feels_like']}°C")
                    with col3:
                        st.metric("💧 Humidity", f"{weather['humidity']}%")
                    with col4:
                        st.metric("☁️ Conditions", weather['description'].title())
                    
                    # Weather advice
                    temp = weather['temperature']
                    if temp > 25:
                        st.info("🌞 Great weather for outdoor activities! Don't forget sunscreen.")
                    elif temp < 10:
                        st.info("🧥 Pack warm clothes - it's quite cold!")
                    else:
                        st.info("👕 Mild weather - perfect for exploring!")
                        
                else:
                    st.error(f"❌ {weather['error']} - Please check the city name and try again.")
        
        # Tab 3: Itinerary
        with tab3:
            st.header("📅 Your Daily Itinerary")
            st.markdown("*Get a detailed day-by-day plan for your trip*")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                destination_for_itinerary = st.text_input(
                    "🗺️ Destination for Itinerary",
                    value=st.session_state.get('destination_city', ''),
                    placeholder="e.g., Rome, New York, Bangkok"
                )
            with col2:
                generate_itinerary = st.button("Generate Plan", type="secondary")
            
            if destination_for_itinerary and (generate_itinerary or st.session_state.get('itinerary_generated')):
                with st.spinner(f"🗓️ Creating your {st.session_state.get('trip_days', 7)}-day itinerary..."):
                    if destination_for_itinerary not in st.session_state.get('itinerary_cache', {}):
                        itinerary = planner.generate_itinerary(
                            destination_for_itinerary, 
                            st.session_state['interests'], 
                            st.session_state['trip_days']
                        )
                        if 'itinerary_cache' not in st.session_state:
                            st.session_state['itinerary_cache'] = {}
                        st.session_state['itinerary_cache'][destination_for_itinerary] = itinerary
                    
                    st.session_state['itinerary_generated'] = True
                    st.write(st.session_state['itinerary_cache'][destination_for_itinerary])
                    st.success("✅ Your personalized itinerary is ready!")
        
        # Tab 4: Packing List
        with tab4:
            st.header("🎒 Smart Packing List")
            st.markdown("*Get a personalized packing list based on your destination and weather*")
            
            if st.session_state.get('weather') and st.session_state.get('destination_city'):
                with st.spinner("👕 Creating your personalized packing list..."):
                    if 'packing_list' not in st.session_state:
                        packing_list = planner.generate_packing_list(
                            st.session_state['destination_city'], 
                            st.session_state['weather'], 
                            st.session_state['trip_days']
                        )
                        st.session_state['packing_list'] = packing_list
                    
                    st.write(st.session_state['packing_list'])
                    st.success("✅ Your packing list is optimized for the weather and activities!")
            else:
                st.info("📍 Please check the weather for your destination first to generate a personalized packing list!")
                if st.button("Go to Weather Tab"):
                    st.experimental_rerun()
        
        # Tab 5: Visa Information
        with tab5:
            st.header("📋 Visa Requirements")
            st.markdown("*Check if you need a visa for your destination*")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                destination_for_visa = st.text_input(
                    "🌍 Destination Country",
                    placeholder="e.g., Japan, Germany, Thailand"
                )
            with col2:
                check_visa = st.button("Check Visa", type="secondary")
            
            if destination_for_visa and st.session_state.get('nationality') and (check_visa or st.session_state.get('visa_checked')):
                with st.spinner("📄 Checking visa requirements..."):
                    visa_info = planner.get_visa_info(destination_for_visa, st.session_state['nationality'])
                    st.session_state['visa_info'] = visa_info
                    st.session_state['visa_checked'] = True
                    
                st.write(visa_info)
                st.warning("⚠️ **Important**: This is general information only. Always verify current requirements with official embassy or consulate sources before traveling!")
                
                # Helpful links
                with st.expander("🔗 Useful Visa Resources"):
                    st.markdown("""
                    - **US Citizens**: [State Department Travel Advisories](https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html)
                    - **General**: [VisaHQ](https://www.visahq.com/) or [iVisa](https://www.ivisa.com/)
                    - **Embassy Finder**: Search "[Country] embassy [your location]"
                    """)
    
    else:
        # Show getting started guide
        st.markdown("### 🚀 How to Get Started")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **1. Set Your Preferences** 👈
            - Choose your budget range
            - Enter departure city
            - Select travel dates
            """)
        
        with col2:
            st.markdown("""
            **2. Pick Your Interests** 🎯
            - Select activities you enjoy
            - Choose preferred climate
            - Add your nationality
            """)
        
        with col3:
            st.markdown("""
            **3. Get Recommendations** ✨
            - Click 'Plan My Trip'
            - Explore the generated tabs
            - Copy destinations between tabs
            """)
    
    # Footer
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Made with ❤️ using AI • Always verify travel information with official sources")
    with col2:
        # API Configuration Help
        with st.expander("⚙️ Setup API Keys"):
            st.markdown("""
            **Need API keys?** Add these to Replit Secrets:
            - `OPENAI_API_KEY` - [Get here](https://platform.openai.com/api-keys)
            - `OPENWEATHER_API_KEY` - [Get here](https://openweathermap.org/api)
            - `GOOGLE_MAPS_API_KEY` - [Get here](https://developers.google.com/maps) (optional)
            """)

if __name__ == "__main__":
    main()
