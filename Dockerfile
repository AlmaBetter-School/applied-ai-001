FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py agent.py models.py tools.py policy.md ./
RUN useradd --create-home appuser
USER appuser
ENV STREAMLIT_CLIENT_TOOLBAR_MODE=viewer
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
