FROM mcr.microsoft.com/devcontainers/python:3.11

RUN apt-get update && apt-get install -y openjdk-17-jdk maven wget unzip && rm -rf /var/lib/apt/lists/*

# Optional SpotBugs CLI install
RUN mkdir -p /opt/spotbugs && \
    wget -qO /tmp/spotbugs.zip https://repo1.maven.org/maven2/com/github/spotbugs/spotbugs/4.8.5/spotbugs-4.8.5.zip && \
    unzip -q /tmp/spotbugs.zip -d /opt && \
    ln -s /opt/spotbugs-4.8.5 /opt/spotbugs && \
    ln -s /opt/spotbugs/bin/spotbugs /usr/local/bin/spotbugs

WORKDIR /workspace
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV SPOTBUGS_PATH=/usr/local/bin/spotbugs
ENV MAVEN_BIN=mvn
ENV WORKSPACE_DIR=/workspace/data/workspace
RUN mkdir -p /workspace/data/workspace /workspace/data/index /workspace/data/export

EXPOSE 8501
CMD ["streamlit", "run", "app/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

