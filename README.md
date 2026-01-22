<div align="center">
  <img src="./static/img/custom-cityscape-banner-filip.jpg" alt="Deadlock Analytics Banner" width="100%">
</div>

# Deadlock Analytics

A comprehensive web-based analytics platform for Deadlock game statistics. View detailed player performance metrics, match history, hero statistics, and interactive visualisations.

## Live Application

🚀 **Try it now**: [https://deadlock-analytics-164941517977.europe-west2.run.app](https://deadlock-analytics-164941517977.europe-west2.run.app)

The application is deployed on **Google Cloud Run** in the `europe-west2` region, providing:
- Auto-scaling from 0 to 10 instances based on traffic
- 2Gi memory and 2 CPU cores per instance
- 120-second timeout for comprehensive data analysis
- Managed with Terraform for infrastructure as code

## Features

- **Player Dashboard**: View Steam profile, rank badge, and summary statistics
- **Performance Analytics**: Track KDA trends with rolling averages over time
- **Hero Statistics**: See your top 5 most-played heroes with win rates
- **Hero Filtering**: Click any hero to filter all stats and charts by that hero (with audio feedback!)
- **MMR History**: Monitor rank progression with smoothed trend lines
- **Community Comparison**: Compare your performance against community percentiles
- **Interactive Charts**: Dynamic visualizations with Plotly for kills, deaths, and performance curves
- **Match Location Analysis**: Visualize kill/death locations on the game map
- **Interactive Audio**: Hero voicelines, UI sounds, and sequential footstep sounds on interactions

## Quick Start

### Prerequisites

- Python 3.12 or higher
- `uv` package manager (or pip)

### Installation

```bash
# Clone the repository
git clone https://github.com/Filpill/deadlock_analytics.git
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

- **Backend**: Flask 3.1+ with Gunicorn WSGI server
- **Data Processing**: pandas, numpy, scipy
- **Visualizations**: Plotly 6.5+
- **API Integration**: Deadlock API (api.deadlock-api.com, assets.deadlock-api.com)
- **Package Management**: uv
- **Deployment**: Google Cloud Run, Docker, Terraform
- **Audio**: Browser Web Audio API with Deadlock game assets

## Project Structure

```
deadlock-analytics/
├── app.py                  # Main Flask application
├── Dockerfile              # Cloud Run optimized Docker image
├── .dockerignore           # Docker build exclusions
├── templates/              # HTML templates
│   ├── index.html         # Landing page
│   └── results.html       # Analytics dashboard
├── static/                 # Static assets (images, fonts)
│   ├── img/               # Minimap, logos, banners
│   └── fonts/             # Custom fonts
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # Cloud Run service configuration
│   ├── variables.tf       # Terraform variables
│   ├── outputs.tf         # Service outputs
│   └── README.md          # Terraform deployment guide
├── scripts/                # Analysis scripts and notebooks
├── pyproject.toml         # Project dependencies
├── uv.lock                # Locked dependency versions
├── CLAUDE.md              # Comprehensive development guide
└── README.md              # This file
```

## API Documentation

This project uses the official Deadlock API:
- **Data API**: https://api.deadlock-api.com/docs
- **Assets API**: https://assets.deadlock-api.com/docs

## Development

For detailed development guidelines, API schema reference, and contribution instructions, see [CLAUDE.md](CLAUDE.md).

## Cloud Deployment

The application is production-ready and deployed to Google Cloud Run using a containerized setup:

### Infrastructure

- **Platform**: Google Cloud Run (fully managed serverless)
- **Region**: europe-west2 (London)
- **Container**: Docker image built with Python 3.12-slim
- **WSGI Server**: Gunicorn with 2 workers and 4 threads
- **Package Manager**: uv for fast dependency installation
- **Infrastructure as Code**: Terraform for repeatable deployments

See `terraform/README.md` for complete Terraform configuration details.

### Service Configuration

The Cloud Run service is configured with:
- **Memory**: 2Gi (sufficient for API responses and data processing)
- **CPU**: 2 cores (handles concurrent requests efficiently)
- **Timeout**: 120 seconds (allows time for Deadlock API calls and chart generation)
- **Scaling**: 0 to 10 instances (scales to zero when idle for cost savings)
- **Authentication**: Public access (no authentication required)

## Acknowledgments

- Powered by [Deadlock API](https://deadlock-api.com)
- Built with Python, Plotly and Flask
