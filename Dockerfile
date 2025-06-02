# Dockerfile
FROM python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1) \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com//${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY scraper.py .
COPY config.py .
COPY run_scraper.py .

# Copy cron job file
COPY crontab /etc/cron.d/scraper-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/scraper-cron

# Apply cron job
RUN crontab /etc/cron.d/scraper-cron

# Create log directory
RUN mkdir -p /var/log/scraper

# Create startup script
COPY start.sh .
RUN chmod +x start.sh

# Expose port for health checks (optional)
EXPOSE 8080

# Start cron and keep container running
CMD ["./start.sh"]
