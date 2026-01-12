import os
import urllib.request

# Base URL for Wikimedia Commons chess pieces (Standard Cburnett style)
BASE_URL = "https://upload.wikimedia.org/wikipedia/commons"

# Map of local filename -> Wikimedia URL path
PIECES = {
    "wP.svg": "/4/45/Chess_plt45.svg",
    "wN.svg": "/7/70/Chess_nlt45.svg",
    "wB.svg": "/b/b1/Chess_blt45.svg",
    "wR.svg": "/7/72/Chess_rlt45.svg",
    "wQ.svg": "/1/15/Chess_qlt45.svg",
    "wK.svg": "/4/42/Chess_klt45.svg",
    "bP.svg": "/c/c7/Chess_pdt45.svg",
    "bN.svg": "/e/ef/Chess_ndt45.svg",
    "bB.svg": "/9/98/Chess_bdt45.svg",
    "bR.svg": "/f/ff/Chess_rdt45.svg",
    "bQ.svg": "/4/47/Chess_qdt45.svg",
    "bK.svg": "/f/f0/Chess_kdt45.svg",
}

# Target directory inside your frontend
TARGET_DIR = os.path.join("frontend", "public", "pieces")

def download_pieces():
    # Ensure the directory exists
    if not os.path.exists(TARGET_DIR):
        print(f"Creating directory: {TARGET_DIR}")
        os.makedirs(TARGET_DIR)

    print(f"Downloading chess pieces to {TARGET_DIR}...")
    
    # Add a User-Agent header to mimic a browser, otherwise Wikimedia blocks the request (403)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    for filename, url_path in PIECES.items():
        full_url = BASE_URL + url_path
        save_path = os.path.join(TARGET_DIR, filename)
        
        print(f"Downloading {filename}...", end="", flush=True)
        try:
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
                out_file.write(response.read())
            print(" Done.")
        except Exception as e:
            print(f" Error: {e}")

    print("\nAll pieces downloaded! You can now refresh your browser.")

if __name__ == "__main__":
    download_pieces()
