# VectorShift Integrations Technical Assessment

This project is a full-stack application designed to integrate with third-party services using OAuth 2.0. It features a Python/FastAPI backend, a React frontend, and uses Redis for temporary data storage.

This submission completes the core requirements of the assessment, which involved implementing a new integration for HubSpot.

## Features Implemented
-   **HubSpot OAuth 2.0 Flow:** Full implementation of the secure authorization code flow for HubSpot.
-   **Credential Management:** Securely handles client secrets using a `.env` file and stores temporary tokens in Redis.
-   **HubSpot Data Loading:** Fetches contact data from the HubSpot CRM API using the acquired access token.
-   **Robust Code:** Includes professional docstrings, type hinting, error handling for network requests, and a clean, readable structure.
-   **Frontend Integration:** A new HubSpot component was created in React and integrated into the existing user interface.

---
## Setup and Installation

### Prerequisites
-   Python 3.8+
-   Node.js v16+
-   Redis

### Backend Setup
1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```
2.  Create and activate a Python virtual environment:
    ```bash
    # Create the venv
    python3 -m venv venv

    # Activate on macOS/Linux
    source venv/bin/activate

    # Activate on Windows
    .\venv\Scripts\activate
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a local environment file. Make a copy of `.env.example` and name it `.env`.
    ```bash
    # On macOS/Linux
    cp .env.example .env

    # On Windows
    copy .env.example .env
    ```
5.  Open the newly created `.env` file and add your HubSpot Client ID and Secret.

### Frontend Setup
1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install the required Node.js packages:
    ```bash
    npm i
    ```

---
## Running the Application

To run the application, you will need to have three separate terminal windows open.

1.  **Terminal 1: Start Redis**
    ```bash
    redis-server
    ```

2.  **Terminal 2: Start the Backend Server**
    ```bash
    # Navigate to the backend directory
    cd backend

    # Activate the virtual environment if it's not already
    # (e.g., source venv/bin/activate)

    # Start the server
    uvicorn main:app --reload
    ```
    The backend will be running on `http://localhost:8000`.

3.  **Terminal 3: Start the Frontend Server**
    ```bash
    # Navigate to the frontend directory
    cd frontend

    # Start the React app
    npm run start
    ```
    The frontend will open automatically in your browser at `http://localhost:3000`.