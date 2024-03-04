from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from huey import RedisHuey
import os

app = FastAPI()

redis_host = os.environ.get("REDIS_HOST", "localhost")
huey = RedisHuey('my-app', host=redis_host)

# In-memory key-value store
store: Dict[str, str] = {}

class Item(BaseModel):
    key: str
    value: str


@huey.task()
def set_key_value(key, value):
    print("Key-value pair set successfully")
    print(f"key: {key}, value: {value}")
    return {"key": key, "value": value}

@huey.task()
def get_key_value(key):
    print(f"Getting value for key: {key}")
    return store.get(key)

@huey.task()
def update_key_value(key, value):
    print(f"Updating value for key: {key}, value: {value}")
    if key not in store:
        return None
    store[key] = value
    return {"key": key, "value": value}

@huey.task()
def delete_key_value(key):
    print(f"Deleting value for key: {key}")
    if key not in store:
        return None
    del store[key]
    return {"message": "Item deleted successfully"}

@app.post("/items/")
def create_item(item: Item):
    if item.key in store:
        raise HTTPException(status_code=400, detail="Item already exists")
    set_key_value(item.key, item.value)
    store[item.key] = item.value
    return {"key": item.key, "value": item.value}


@app.get("/items/{key}")
def read_item(key: str):
    if key not in store:
        raise HTTPException(status_code=404, detail="Item not found")
    get_key_value(key)
    return {"key": key, "value": store[key]}


@app.put("/items/{key}")
def update_item(key: str, item: Item):
    if key not in store:
        raise HTTPException(status_code=404, detail="Item not found")
    store[key] = item.value
    update_key_value(key, item.value)
    return {"key": key, "value": item.value}


@app.delete("/items/{key}")
def delete_item(key: str):
    if key not in store:
        raise HTTPException(status_code=404, detail="Item not found")
    del store[key]
    return {"message": "Item deleted successfully"}


# Import and run the consumer
from huey.consumer import Consumer
consumer = Consumer(huey, workers=1)
consumer.run()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
