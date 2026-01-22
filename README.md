<div align="center">
  <img src="./static/img/custom-cityscape-banner-filip.png" alt="Deadlock Analytics Banner" width="100%">
</div>

# Deadlock Analytics

A comprehensive web-based analytics platform for Deadlock game statistics. View detailed player performance metrics, match history, hero statistics, and interactive visualizations with a Steam-themed interface.

## Features

- **Player Dashboard**: View Steam profile, rank badge, and summary statistics
- **Performance Analytics**: Track KDA trends with rolling averages over time
- **Hero Statistics**: See your top 5 most-played heroes with win rates
- **MMR History**: Monitor rank progression with smoothed trend lines
- **Community Comparison**: Compare your performance against community percentiles
- **Interactive Charts**: Dynamic visualizations with Plotly for kills, deaths, and performance curves
- **Match Location Analysis**: Visualize kill/death locations on the game map

## Quick Start

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (or pip)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd deadlock-analytics

# Install uv (if not already installed)
pip install uv

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

### Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Flask app
python app.py

# Open browser to http://localhost:5000
```

### Usage

1. Enter your **Player ID** (SteamID3 format, e.g., `199540209`)
2. Click **Analyze Player Stats**
3. View your personalized analytics dashboard

## Technology Stack

- **Backend**: Flask 3.1+
- **Data Processing**: pandas, numpy, scipy
- **Visualizations**: Plotly 6.5+
- **API Integration**: Deadlock API (api.deadlock-api.com)
- **Package Management**: uv

## Project Structure

```
deadlock-analytics/
├── app.py                  # Main Flask application
├── templates/              # HTML templates
│   ├── index.html         # Landing page
│   └── results.html       # Analytics dashboard
├── static/                 # Static assets (images)
├── scripts/                # Analysis scripts and notebooks
├── pyproject.toml         # Project dependencies
└── README.md              # This file
```

## API Documentation

This project uses the official Deadlock API:
- **Data API**: https://api.deadlock-api.com
- **Assets API**: https://assets.deadlock-api.com
- **Documentation**: https://api.deadlock-api.com/docs

## Development

For detailed development guidelines, API schema reference, and contribution instructions, see [CLAUDE.md](CLAUDE.md).

## License

[Add your license here]

## Acknowledgments

- Powered by [Deadlock API](https://deadlock-api.com)
- Built with Python and Flask
