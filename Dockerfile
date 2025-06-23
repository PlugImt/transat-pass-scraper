# Dockerfile
FROM python:3.12

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    cron \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Detect architecture and install Chrome accordingly
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        # AMD64 installation
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
        && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update \
        && apt-get install -y google-chrome-stable; \
    else \
        # ARM64/other architectures - use Chromium instead
        apt-get update \
        && apt-get install -y chromium chromium-driver; \
    fi \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver for AMD64, or use system chromium-driver for ARM64
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1) \
        && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}") \
        && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
        && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
        && chmod +x /usr/local/bin/chromedriver \
        && rm /tmp/chromedriver.zip; \
    else \
        # For ARM64, chromium-driver is already installed and in PATH
        echo "Using system chromium-driver for ARM64"; \
    fi

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY .env .
COPY api_client.py .
COPY config.py .
COPY run_scraper.py .
COPY scraper.py .
COPY steps ./steps/

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