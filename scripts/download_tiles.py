import os
import math
import time
import requests
from pathlib import Path

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def download_tiles():
    # Bounding box covering Upper Assam wells
    min_lat, max_lat = 27.1, 27.7
    min_lon, max_lon = 94.8, 95.5
    
    zooms = range(8, 15)  # 8 to 14
    
    base_url = "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"
    output_dir = Path(__file__).resolve().parent.parent / "backend" / "static" / "tiles"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    total_downloaded = 0
    total_skipped = 0
    total_failed = 0
    
    print(f"Downloading tiles to {output_dir}")
    
    for z in zooms:
        # Get tile range
        xmin, ymax = deg2num(min_lat, min_lon, z)
        xmax, ymin = deg2num(max_lat, max_lon, z)
        
        # Ensure correct min/max ordering
        x_start, x_end = min(xmin, xmax), max(xmin, xmax)
        y_start, y_end = min(ymin, ymax), max(ymin, ymax)
        
        for x in range(x_start, x_end + 1):
            for y in range(y_start, y_end + 1):
                url = base_url.format(z=z, x=x, y=y)
                tile_dir = output_dir / str(z) / str(x)
                tile_dir.mkdir(parents=True, exist_ok=True)
                
                tile_path = tile_dir / f"{y}.png"
                if tile_path.exists():
                    total_skipped += 1
                    continue
                
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    with open(tile_path, "wb") as f:
                        f.write(response.content)
                        
                    total_downloaded += 1
                    time.sleep(0.05)  # Be polite to the tile server
                except Exception as e:
                    print(f"Failed to download {url}: {e}")
                    total_failed += 1

    print(f"Finished! Downloaded: {total_downloaded}, Skipped: {total_skipped}, Failed: {total_failed}")

if __name__ == "__main__":
    download_tiles()
