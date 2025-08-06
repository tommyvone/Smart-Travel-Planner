
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
    st.markdown("Plan your perfect trip with AI-powered recommendations!")
    
    # Initialize the travel planner
    planner = TravelPlanner()
    
    # Sidebar for user inputs
    st.sidebar.header("✈️ Your Travel Preferences")
    
    # User input collection
    budget = st.sidebar.selectbox(
        "Budget Range",
        ["Budget ($0-$1000)", "Mid-range ($1000-$3000)", "Luxury ($3000+)"]
    )
    
    departure_city = st.sidebar.text_input("Departure City", "New York")
    
    zip_code = st.sidebar.text_input(
        "📍 Your Zip Code (Optional)", 
        placeholder="12345",
        help="Enter your zip code for more accurate location-based recommendations"
    )
    
    travel_dates = st.sidebar.date_input(
        "Travel Dates",
        value=(datetime.now().date(), datetime.now().date() + timedelta(days=7)),
        help="Select start and end dates"
    )
    
    interests = st.sidebar.multiselect(
        "Interests",
        ["Beaches", "Museums", "Hiking", "Food", "Nightlife", "History", "Shopping", "Adventure Sports", "Wildlife", "Architecture"],
        default=["Beaches", "Food"]
    )
    
    climate = st.sidebar.selectbox(
        "Preferred Climate",
        ["Warm", "Cool", "Tropical", "Temperate", "No preference"]
    )
    
    nationality = st.sidebar.text_input("Your Nationality", "American")
    
    # Calculate trip duration
    if len(travel_dates) == 2:
        trip_days = (travel_dates[1] - travel_dates[0]).days
    else:
        trip_days = 7
    
    # Main interface tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎯 Destinations", "🌤️ Weather", "📅 Itinerary", "🎒 Packing", "📋 Visa Info"])
    
    if st.sidebar.button("🚀 Plan My Trip", type="primary"):
        # Store zip code in session state
        if zip_code:
            st.session_state['zip_code'] = zip_code
            
        with st.spinner("Planning your amazing trip..."):
            
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
                
                # Simple destination input for weather
                destination_for_weather = st.text_input(
                    "Enter destination city for weather:",
                    help="Enter a city name from the recommended destinations"
                )
                
                if destination_for_weather:
                    weather = planner.get_weather_forecast(destination_for_weather)
                    if "error" not in weather:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Temperature", f"{weather['temperature']}°C")
                        with col2:
                            st.metric("Feels Like", f"{weather['feels_like']}°C")
                        with col3:
                            st.metric("Humidity", f"{weather['humidity']}%")
                        
                        st.info(f"Weather: {weather['description'].title()}")
                        st.session_state['weather'] = weather
                        st.session_state['destination_city'] = destination_for_weather
                    else:
                        st.error(weather['error'])
            
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
    with st.expander("🔧 API Configuration Help"):
        st.markdown("""
        To use all features of this app, you'll need API keys for:
        
        1. **OpenAI API** - For destination suggestions, itineraries, and packing lists
        2. **OpenWeatherMap API** - For weather forecasts (free tier available)
        3. **Google Maps API** - For location services (optional)
        
        Add these to your Replit Secrets or environment variables:
        - `OPENAI_API_KEY`
        - `OPENWEATHER_API_KEY`
        - `GOOGLE_MAPS_API_KEY`
        """)

if __name__ == "__main__":
    main()
