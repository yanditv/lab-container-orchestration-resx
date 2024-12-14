FROM python:slim-buster AS base
RUN useradd -Um worker
RUN apt-get update \
&& apt-get install -yq jq \
&& apt-get clean

FROM python:slim-buster AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --upgrade pip \
&& python3 -m pip install wheel \
&& python3 -m pip install --disable-pip-version-check --no-cache-dir -r /tmp/requirements.txt

FROM base
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
USER worker
WORKDIR /app
COPY --chown=worker . .
ENV PORT=8000
EXPOSE 8000
RUN whereis uvicorn
ENTRYPOINT sh -c 'uvicorn --proxy-headers --port $PORT --host "0.0.0.0" main:app'
