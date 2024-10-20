## TFL Alerts

This bot is used to monitor the status of the London Underground and publish alerts to Threads.

### How it works

1. The bot fetches the status of all lines from the TFL API.
2. It then checks if any of the lines have changed status.
3. If a line has changed status, it will publish a post to Threads.

### Setup and Installation

1. Install Python 3 and python3-venv if not already installed:
   ```
   sudo apt-get update
   sudo apt-get install python3 python3-venv
   ```

2. Create a virtual environment:
   ```
   python3 -m venv .venv
   ```

3. Activate the virtual environment:
   ```
   source .venv/bin/activate
   ```

### How to run

1. Set the environment variables in the `.env` file.
2. Ensure your virtual environment is activated.
3. Run the script with `python tfl_api.py`.
