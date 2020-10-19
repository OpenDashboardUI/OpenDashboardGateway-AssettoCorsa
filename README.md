# OpenDashboardGateway-AssettoCorsa

Gateway to forward telemetry data from AssettoCorsa racing simulation to OpenDashboard.

## Setup virtual environment
    python -m venv .venv
    source .venv/bin/activate

## Build and pack
    python setup.py protoc
    python setup.py shiv