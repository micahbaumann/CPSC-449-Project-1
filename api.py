# This file contains starter code for the project

from fastapi import FastAPI

app = FastAPI()

# This is an example endpoint. Change the "/" to the path. For example: "/listclasses"
# For each new endpoint here, create a new endpoint in the etc/krakend.json file
@app.get("/")
def read_root():
    return {"Hello": "World"}