api: uvicorn --port $PORT api:app --reload
krakend: echo ./etc/krakend.json | entr -nrz krakend run --port $PORT --config etc/krakend.json
