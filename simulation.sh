#!/bin/bash

# STEP 1: Start containers
docker compose up -d --build
echo "🟢 Containers started. Waiting 5s for services to warm up..."
sleep 5

# STEP 2: Simulate traffic
mkdir -p logs
> logs/edge1.csv
> logs/cdn.csv

echo "🚀 Simulating 100 requests to edge1.local"
for i in {1..100}; do
  curl -s -o /dev/null -w "%{time_total},%{size_download},%{http_code}\n" \
    http://edge1.local:8082/books/book$(( (i % 3) + 1 )).pdf >> logs/edge1.csv
done

echo "🚀 Simulating 100 requests to cdn.local"
for i in {1..100}; do
  curl -s -o /dev/null -w "%{time_total},%{size_download},%{http_code}\n" \
    http://cdn.local:8081/books/book$(( (i % 3) + 1 )).pdf >> logs/cdn.csv
done

# STEP 3: Collect logs
docker exec edge1 cat /var/log/nginx/access.log > logs/edge1_access.log
docker exec edge cat /var/log/nginx/access.log > logs/cdn_access.log

# STEP 4: Analyze
python3 energy_model.py logs/edge1.csv logs/edge1_access.log edge1
python3 energy_model.py logs/cdn.csv logs/cdn_access.log cdn

echo "✅ All done! Energy comparison chart saved as energy_report.png"