from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function 1: Use OpenAI to classify the query as 'greeting', 'relevant', or 'irrelevant'.

def classify_query(query):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"""
You are an intelligent query classifier for a running and fitness chatbot. Your role is to analyze the user's query and classify it into one of three categories:
- 'greeting': The user is starting the conversation with a casual or formal greeting. This could be slang as well.
- 'relevant': The user is asking a question directly related to their activities, running, cycling (riding), fitness, training, or performance nutrition. 
- 'irrelevant': The query is unrelated to fitness or training, such as asking about food recipes, math problems, or general knowledge.

Only return the single word, unstyled, no markup, just 'greeting', 'relevant', or 'irrelevant'. Nothing else.

User query: '{query}'
"""
                }
            ]
        )
        # Extract and clean the model's response
        classification = response.choices[0].message.content.strip().lower()

        # Normalize response to ensure it matches one of the valid categories
        classification = classification.strip(" '\"")  # Remove quotes or unexpected characters

        # Validate the response is an exact match to expected categories
        valid_categories = {"greeting", "relevant", "irrelevant"}
        if classification in valid_categories:
            return classification

        # Handle unexpected responses
        print(f"Unexpected classification response: {classification}")  # Debug log
        return "unknown"
    except Exception as e:
        print(f"Error in classify_query: {e}")
        return "unknown"

# Function 2: Create the prompt later sent to the GPT

def create_prompt(activities_csv, user_query, max_activities=200):
    # Add explanation for the CSV format
    csv_explanation = """
    The activity data is presented in the following csv format:
    - Activity Type: Either 'Run' or 'Ride'.
    - Name: Name of the activity.
    - Distance: Distance in kilometers (km).
    - Elevation Gain: Elevation gain in meters (m).
    - Avg HR: Average heart rate in beats per minute (bpm).
    - Pace/Speed: For 'Run' activities, this is the average pace in minutes per kilometer (min/km). For 'Ride' activities, this is the average speed in kilometers per hour (km/h).
    - Duration: Duration of the activity in minutes (min).
    """
    # Ensure the activities are split into lines
    activities_list = activities_csv.splitlines()

    # Truncate activities to the maximum allowed
    activity_data = "\n".join(activities_list[:max_activities])

    # Combine explanation and data into the prompt
    prompt = f"""
You are a virtual running coach for a web app. Your purpose is to provide advice on whatever the user asks, whether that's running, cycling, training, or performance nutrition. Structure your response using simple sentences and clear spacing. Ensure that your response uses clear paragraphs with line breaks to separate ideas, making the information easy to read. Use a conversational and encouraging tone, while staying concise, clear, and actionable.

{csv_explanation}

Here is the user's recent training data:
{activity_data}

User question: {user_query}

Provide a tailored, well-structured and clear response based on the user's recent training. Respond as a natural human being. Do not respond like ChatGPT. Do not respond like a robot. Do not use unneccesary capital letters in headings. Do not use any markdown like ***bold*** or ### italic. Do not use lists.
"""
    return prompt

# Function 3: Create the actual query sent to the GPT

def query_openai(prompt, max_tokens=900):

    max_tokens = int(max_tokens)  # Explicitly cast to integer
    
    # Debugging print statement
    print(f"Prompt sent to GPT:\n{prompt}")  # Print the full prompt for debugging

    # Send to GPT
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in query_openai: {e}")
        return "Sorry, I couldn't process your request. Please try again."

# Function 4: Get greeting response

def get_greeting_response(user_input):
    try:
        # Define the GPT prompt
        prompt = f"""
        You are a virtual assistant specializing in running, cycling, swimming, and fitness. You are part of a fitness dashboard web app built with the Strava API, so always act as if you already have access to the user's fitness data, including their recent activities and training progress. When responding to greetings, tailor your responses naturally and contextually while subtly reinforcing that you are ready to assist with their fitness journey. Keep your greeting short. Always sound confident, encouraging, and ready to assist with their training.

        User's input: {user_input}
        """
        
        # Send the prompt to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,  # Keep the response concise
            temperature=0.7
        )
        
        # Extract the response text
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in get_greeting_response: {e}")
        return "Sorry, I couldn't process your greeting. How can I assist you with your training?"