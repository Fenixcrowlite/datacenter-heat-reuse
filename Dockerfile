FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HEAT_REUSE_RUNTIME=/data
WORKDIR /app
COPY heat_reuse ./heat_reuse
COPY tools ./tools
COPY web ./web
COPY datasets ./datasets
COPY models ./models
COPY docs ./docs
COPY tests ./tests
COPY original ./original
RUN useradd --uid 10001 --create-home laboratory && mkdir /data && chown laboratory:laboratory /data
USER laboratory
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health',timeout=3)"
CMD ["python", "-m", "heat_reuse", "serve", "--host", "0.0.0.0", "--port", "8080"]
