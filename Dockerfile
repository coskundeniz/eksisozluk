FROM python:3.9

# Set the working directory to /src
WORKDIR /src

# Copy the project directory into /src
COPY . /src

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# install requirements
RUN pip install --no-cache-dir --trusted-host pypi.python.org -r requirements.txt

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get update && apt-get install -y google-chrome-stable && rm -rf /var/lib/apt/lists/*

# set display port to avoid crash
ENV DISPLAY=:99

# Run the script when the container launches
ENTRYPOINT ["python", "eksisozluk.py"]
