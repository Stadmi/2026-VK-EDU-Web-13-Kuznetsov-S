#!/bin/bash
# Запускать внутри контейнера: docker compose exec web bash benchmark.sh
# Или установить apache2-utils: apt-get install -y apache2-utils

echo "=== 1. Static via nginx ==="
ab -n 1000 -c 10 http://nginx/sample.html

echo "=== 2. Static via gunicorn (Django DEBUG staticfiles) ==="
ab -n 1000 -c 10 http://localhost:8000/static/sample.html

echo "=== 3. Dynamic via gunicorn (direct) ==="
ab -n 1000 -c 10 http://localhost:8000/

echo "=== 4. Dynamic via nginx -> gunicorn (no cache, first run) ==="
ab -n 1000 -c 10 http://nginx/

echo "=== 5. Dynamic via nginx -> gunicorn (proxy_cache active) ==="
ab -n 1000 -c 10 http://nginx/
