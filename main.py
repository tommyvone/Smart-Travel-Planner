from flask import Flask, render_template, request, jsonify
import openai
import requests
import googlemaps
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any

app = Flask(__name__)

class TravelPlanner:
    def __init__(self):
        self.openai_client = None
        self.gmaps = None
        self.weather_api_key = None
        self.setup_apis()

    def setup_apis(self):
        """Initialize API clients"""
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
            self.weather_api_key = os.getenv("OPENWEATHER_API_KEY")

            print(f"🔍 Debugging OpenAI API key:")
            print(f"   - Key exists: {'Yes' if openai_key else 'No'}")
            if openai_key:
                print(f"   - Key length: {len(openai_key)}")
                print(f"   - Key starts with 'sk-': {'Yes' if openai_key.startswith('sk-') else 'No'}")
                print(f"   - Key preview: {openai_key[:10]}...{openai_key[-4:] if len(openai_key) > 14 else ''}")

            if openai_key and len(openai_key) > 10:  # Basic validation
                try:
                    self.openai_client = openai.OpenAI(api_key=openai_key)
                    print("✅ OpenAI client initialized successfully")

                    # Test the client with a simple request
                    try:
                        test_response = self.openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": "Hello"}],
                            max_tokens=5
                        )
                        print("✅ OpenAI API test successful")
                    except Exception as test_error:
                        print(f"⚠️ OpenAI API test failed: {test_error}")

                except Exception as openai_error:
                    print(f"❌ OpenAI client failed to initialize: {openai_error}")
                    self.openai_client = None
            else:
                print("❌ OpenAI API key not found or invalid")
                if not openai_key:
                    print("   - Check that you have a secret named exactly 'OPENAI_API_KEY'")
                elif len(openai_key) <= 10:
                    print(f"   - Key too short ({len(openai_key)} characters)")

            if google_maps_key:
                try:
                    self.gmaps = googlemaps.Client(key=google_maps_key)
                    print("✅ Google Maps client initialized successfully")
                except Exception as gmaps_error:
                    print(f"⚠️ Google Maps client failed ({type(gmaps_error).__name__}): {gmaps_error}")
                    print("   - Continuing without Google Maps (this won't affect OpenAI functionality)")
                    self.gmaps = None
            else:
                print("ℹ️  Google Maps API key not found (optional)")

            if self.weather_api_key:
                print("✅ Weather API key found")
            else:
                print("❌ Weather API key not found (optional)")

        except Exception as e:
            print(f"Error setting up APIs: {e}")

    def get_api_status(self):
        """Check which APIs are configured"""
        return {
            'openai': self.openai_client is not None,
            'weather': self.weather_api_key is not None,
            'google_maps': self.gmaps is not None
        }

    def get_destination_suggestions(self, budget: str, interests: List[str], climate: str, departure_city: str, zip_code: str = "") -> str:
        """Get travel destination suggestions using OpenAI"""
        if not self.openai_client:
            return """🚀 Welcome to Smart Travel Planner! 

To get personalized travel recommendations, you'll need to add your OpenAI API key:

🔑 How to add your API key:
1. Get a free API key from OpenAI at: https://platform.openai.com/api-keys
2. In Replit, click on 'Tools' in the left sidebar
3. Select 'Secrets' from the tools menu
4. Click '+ New Secret'
5. Set the key name to: OPENAI_API_KEY
6. Paste your API key as the value
7. Click 'Add Secret'
8. Refresh this page and try again!

Once set up, I'll be able to create amazing travel plans just for you! ✈️"""

        try:
            location_info = departure_city
            if zip_code:
                location_info = f"{departure_city} (Zip: {zip_code})"

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

            Format as a clear, readable list with proper line breaks.
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
            return "🔑 Please add your OpenAI API key to Replit Secrets to generate itineraries. See the main page for setup instructions!"

        try:
            prompt = f"""
            Create a detailed {days}-day itinerary for {destination} based on these interests: {', '.join(interests)}.

            For each day, include:
            - Morning activity
            - Afternoon activity
            - Evening activity
            - Recommended restaurants
            - Transportation tips

            Format as Day 1, Day 2, etc. with clear sections and proper line breaks.
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
            return "🎒 Please add your OpenAI API key to Replit Secrets to generate packing lists. See the main page for setup instructions!"

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
            return "📋 Please add your OpenAI API key to Replit Secrets to get visa information. See the main page for setup instructions!"

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

# Initialize the travel planner
planner = TravelPlanner()

@app.route('/')
def index():
    api_status = planner.get_api_status()
    return render_template('index.html', api_status=api_status)

@app.route('/plan', methods=['POST'])
def plan_trip():
    data = request.json

    departure_city = data.get('departure_city', 'New York')
    zip_code = data.get('zip_code', '')
    nationality = data.get('nationality', 'American')
    budget = data.get('budget', 'Mid-range ($1000-$3000)')
    interests = data.get('interests', [])
    climate = data.get('climate', 'No preference')
    trip_days = int(data.get('trip_days', 7))

    # Get destination suggestions
    destinations = planner.get_destination_suggestions(budget, interests, climate, departure_city, zip_code)

    return jsonify({
        'success': True,
        'destinations': destinations
    })

@app.route('/weather', methods=['POST'])
def get_weather():
    data = request.json
    city = data.get('city', '')

    if not city:
        return jsonify({'error': 'City is required'})

    weather = planner.get_weather_forecast(city)
    return jsonify(weather)

@app.route('/itinerary', methods=['POST'])
def get_itinerary():
    data = request.json
    destination = data.get('destination', '')
    interests = data.get('interests', [])
    days = int(data.get('days', 7))

    if not destination:
        return jsonify({'error': 'Destination is required'})

    itinerary = planner.generate_itinerary(destination, interests, days)
    return jsonify({'itinerary': itinerary})

@app.route('/packing', methods=['POST'])
def get_packing_list():
    data = request.json
    destination = data.get('destination', '')
    weather = data.get('weather', {})
    days = int(data.get('days', 7))

    if not destination:
        return jsonify({'error': 'Destination is required'})

    packing_list = planner.generate_packing_list(destination, weather, days)
    return jsonify({'packing_list': packing_list})

@app.route('/visa', methods=['POST'])
def get_visa_info():
    data = request.json
    destination = data.get('destination', '')
    nationality = data.get('nationality', 'American')

    if not destination:
        return jsonify({'error': 'Destination is required'})

    visa_info = planner.get_visa_info(destination, nationality)
    return jsonify({'visa_info': visa_info})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)