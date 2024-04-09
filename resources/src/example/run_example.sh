#!/bin/bash
ENVIRONMENT=production python resources/src/__main__.py &
sleep 10
python_pid=$!
model="dHJhZmZpYw=="
json_file_path="resources/src/example/example_data.json"
encoded_json=$(base64 -w 0 < "$json_file_path")
curl -X POST -d "model=${model}&data=${encoded_json}" --max-time 10 http://localhost:39091/api/v1/outliers
kill $python_pid
