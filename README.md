# Crypto Arbitrage Dashboard

This project is a cryptocurrency arbitrage scanner that identifies and visualizes arbitrage opportunities across multiple exchanges. It fetches real-time price data, calculates potential profits, and displays the results in a user-friendly dashboard using Streamlit.

## Project Structure

```
crypto-arbitrage-dashboard
├── src
│   ├── __init__.py
│   ├── arbitrage_scanner.py
│   ├── exchanges.py
│   └── config.py
├── app.py
├── requirements.txt
├── Procfile
├── .streamlit
│   └── config.toml
├── .gitignore
├── README.md
└── tests
    └── test_arbitrage.py
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd crypto-arbitrage-dashboard
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application locally:**
   ```bash
   streamlit run app.py
   ```

## Usage

- The application will start a local server, and you can access the dashboard in your web browser at `http://localhost:8501`.
- The dashboard will display any arbitrage opportunities found across the specified cryptocurrency exchanges.

## Deployment on Render.com

To deploy the application on Render.com, follow these steps:

1. Ensure you have a Render.com account and create a new web service.
2. Connect your GitHub repository containing the project.
3. Set the build command to:
   ```
   pip install -r requirements.txt
   ```
4. Set the start command to:
   ```
   streamlit run app.py
   ```
5. Deploy the service and monitor the logs for any issues.

## Testing

Unit tests for the arbitrage scanner functionality are located in the `tests/test_arbitrage.py` file. Ensure to run these tests to verify that the core logic works as intended.

## Important Notes

- This project is for educational purposes and should not be considered financial advice.
- Always test the application locally before deploying to ensure everything works as expected.