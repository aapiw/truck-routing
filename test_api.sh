#!/bin/bash
curl -v -X POST "https://truck-routing-ubko.onrender.com/api/routes/analyze/" \
  -H "Content-Type: application/json" \
  -d '{"origin":{"lat":39.7392,"lon":-104.9903},"destination":{"lat":32.7767,"lon":-96.7970},"load_weight":35000}' 2>&1