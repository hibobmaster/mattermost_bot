FROM python:3.11-alpine as base

FROM base as builder
# RUN sed -i 's|v3\.\d*|edge|' /etc/apk/repositories
RUN apk update && apk add --no-cache gcc musl-dev libffi-dev git
COPY requirements.txt .
RUN pip install -U pip setuptools wheel && pip install --user -r ./requirements.txt && rm ./requirements.txt

FROM base as runner
RUN apk update && apk add --no-cache libffi-dev
COPY --from=builder /root/.local /usr/local
COPY . /app

FROM runner
WORKDIR /app
CMD ["python", "main.py"]
