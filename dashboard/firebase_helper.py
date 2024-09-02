import requests
import json

# Firebase configuration
FIREBASE_URL = 'https://dispencer-iot-default-rtdb.asia-southeast1.firebasedatabase.app'
FIREBASE_SECRET = 'AIzaSyCpbWXj1YFZUL7_hVKSZ3-Zv0U9Sb-hYeg'  # Obtain from Firebase Console

def firebase_get(path):
    """Get data from Firebase Realtime Database."""
    url = f"{FIREBASE_URL}{path}.json?auth={FIREBASE_SECRET}"
    response = requests.get(url)
    return response.json()

def firebase_post(path, data):
    """Post data to Firebase Realtime Database."""
    url = f"{FIREBASE_URL}{path}.json?auth={FIREBASE_SECRET}"
    response = requests.post(url, data=json.dumps(data))
    return response.json()

def firebase_put(path, data):
    """Update data in Firebase Realtime Database."""
    url = f"{FIREBASE_URL}{path}.json?auth={FIREBASE_SECRET}"
    response = requests.put(url, data=json.dumps(data))
    return response.json()

def firebase_delete(path):
    """Delete data from Firebase Realtime Database."""
    url = f"{FIREBASE_URL}{path}.json?auth={FIREBASE_SECRET}"
    response = requests.delete(url)
    return response.json()
