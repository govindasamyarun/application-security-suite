FROM python:3.9.1

# Install dependencies 
RUN apt-get update && apt-get install -y netcat

# Create application user 
RUN useradd -ms /bin/bash as2 && \
    usermod -aG sudo as2

# Copy the source code to application home directory 
ADD . /usr/src/app/

# Limit the application user privilege 
RUN chown -R as2:as2 /usr/src/app && \
    chmod -R 764 /usr/src/app

# Run the container as non-root user 
USER as2

# Create empty directories 
RUN mkdir -p /usr/src/app/gitleaks/ && \
    mkdir -p /usr/src/app/downloads/

# Download gitleaks 
WORKDIR /usr/src/app/gitleaks/
RUN wget https://github.com/zricethezav/gitleaks/releases/download/v8.11.2/gitleaks_8.11.2_linux_x64.tar.gz && \
    tar -xvzf gitleaks_8.11.2_linux_x64.tar.gz

# Set the working directory 
WORKDIR /usr/src/app/

# Install python dependencies 
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir -r /usr/src/app/requirements.txt

# Start the application  
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]