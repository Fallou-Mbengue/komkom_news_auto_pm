# Use a lightweight Python image compatible with Scrapy (Python 3.11 is fine)
FROM python:3.11-slim-buster

# Set the working directory inside the container
WORKDIR /app/scraper

# Copy the Scrapy project configuration and source code
# scrapy.cfg is at the root of the Scrapy project (e.g., deep_research/komkom_scraper/)
COPY scrapy.cfg .
# The 'komkom_scraper' folder contains the Python modules of the Scrapy project (settings, spiders, etc.)
COPY komkom_scraper/ komkom_scraper/

# Install Python dependencies directly, as requirements.txt is in a different context.
# Ensure all necessary packages for Scrapy, PostgreSQL interaction, and date parsing are here.
RUN pip install --no-cache-dir \
    scrapy \
    psycopg2-binary \
    python-dateutil \
    sqlalchemy \
    selenium # Added explicitly for Google Search Scraper

# Install Chromium and Chromedriver for headless Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy the new scrapers directory
COPY ../scrapers/ scrapers/

# Default command if no command is specified when running the container (will be overridden by 'docker run')
CMD ["scrapy"]
