# Crypto Arbitrage Scanner

A cryptocurrency arbitrage scanner that identifies and visualizes arbitrage opportunities across multiple exchanges. It fetches price data, calculates potential profits, and displays the results in a Streamlit dashboard.

## Project structure

```
arbitrage_scanner
├── src
│   ├── __init__.py
│   ├── arbitrage_scanner.py
│   ├── exchanges.py
│   └── config.py
├── app.py
├── requirements.txt
├── .streamlit
│   └── config.toml
├── .gitignore
├── README.md
└── tests
    └── test_arbitrage.py
```

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd arbitrage_scanner
```

2. Create a virtual environment:

- Windows (PowerShell / CMD):
```powershell
python -m venv venv
venv\Scripts\Activate.ps1   # PowerShell
venv\Scripts\activate.bat   # CMD
```

- macOS / Linux:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run locally:
```bash
streamlit run app.py
```
Open the dashboard at http://localhost:8501

## Testing

Run unit tests:
```bash
pytest
```

## Deployment (example: Render.com)

- Build command:
```
pip install -r requirements.txt
```
- Start command:
```
streamlit run app.py
```

## Notes

- Educational use only; not financial advice.
- If the repository structure differs from the tree above, provide the current tree and I will update this README accordingly.