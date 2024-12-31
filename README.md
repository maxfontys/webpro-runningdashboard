# Training Dashboard Project

A running and training dashboard powered by **Strava API**, **OpenAI API**, and **React**. The application visualizes user activities, calculates statistics, and integrates a chatbot for fitness advice.

## Features

- **Dashboard**: Displays recent activities, weekly stats, heart rate trends, and training zones.
- **Chatbot**: AI assistant to answer running and fitness-related queries.
- **Settings**: Configurable heart rate zones and max HR.
- **Responsive Design**: Built using **React** and styled with **Tailwind CSS**.
- **Data Integration**: Fetches and processes data from Strava API.


## Installation

### Backend (Python & Flask)

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/webpro-runningdashboard.git
   cd webpro-runningdashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Mac/Linux
   venv\\Scripts\\activate     # Windows
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root:
     ```plaintext
     FLASK_APP=run.py
     FLASK_ENV=development
     OPENAI_API_KEY=your_openai_api_key
     SECRET_KEY=your_flask_secret_key
     STRAVA_CLIENT_ID=your_strava_client_id
     STRAVA_CLIENT_SECRET=your_strava_client_secret
     STRAVA_REDIRECT_URI=http://127.0.0.1:5000/callback
     ```

5. Run the Flask application:
   ```bash
   flask run
   ```

### Frontend (React)

1. Navigate to the React folder:
   ```bash
   cd react-modal
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. For production builds:
   ```bash
   npm run build
   ```

## Tech Stack

### Backend
- **Flask**: Web framework.
- **Flask-CORS**: Cross-Origin Resource Sharing.
- **Python-dotenv**: Environment variable management.
- **OpenAI API**: Chatbot functionality.
- **Strava API**: Activity data integration.

### Frontend
- **React**: UI framework.
- **Radix UI**: Accessible UI components.
- **Tailwind CSS**: Styling.
- **Vite**: Build tool for fast development.



## Project Structure

```plaintext
webpro-runningdashboard/
├── app/                    # Flask application
│   ├── __init__.py         # Flask initialization
│   ├── routes/             # Routes (auth, dashboard, API)
│   ├── services/           # Strava API, chatbot, stats calculations
│   ├── models/             # Data models and settings
│   └── utils/              # Helper functions
├── react-modal/            # Frontend React app
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
├── .env                    # Environment variables
├── requirements.txt        # Backend dependencies
├── package.json            # Frontend dependencies
└── README.md               # Documentation
```

## Usage

1. **Log In**: Authenticate via Strava to fetch your activities.
2. **Explore the Dashboard**:
   - View weekly stats, activity trends, and heart rate data.
   - Interact with the AI chatbot for fitness advice.
3. **Modify Settings**: Adjust heart rate zones or max HR via the settings modal.

## Contributing

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your message here"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Submit a pull request.


## Questions?

Feel free to reach out at **max.jt.yang@gmail.com** for any inquiries.