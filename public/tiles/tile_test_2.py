import os
import requests
import subprocess
from osgeo import ogr

# KMZ file URL
kmz_url = "https://s3.us-west-2.amazonaws.com/tetoncountywy/gis/download/kmz/ownership.kmz"

# Output directories
output_directory = "tile_dir"
os.makedirs(output_directory, exist_ok=True)

def download_file(url, output_path):
    """Download a file from a URL."""
    response = requests.get(url)
    with open(output_path, 'wb') as file:
        file.write(response.content)

def convert_kmz_to_geojson(kmz_file_path, geojson_file_path_base, simplify_tolerance=0.001):
    driver = ogr.GetDriverByName('LIBKML')
    datasource = driver.Open(kmz_file_path, 0)  # Open the KMZ file
    if datasource is None:
        print(f"Failed to open KMZ file: {kmz_file_path}")
        return None

    # Process each layer in the KMZ file
    for i in range(datasource.GetLayerCount()):
        layer = datasource.GetLayerByIndex(i)
        layer_name = layer.GetName()

        # Construct the GeoJSON file path for each layer
        geojson_file_path = os.path.join(output_directory, f"{geojson_file_path_base}_{layer_name}.geojson")

        geojson_driver = ogr.GetDriverByName('GeoJSON')
        if os.path.exists(geojson_file_path):
            geojson_driver.DeleteDataSource(geojson_file_path)

        geojson_datasource = geojson_driver.CreateDataSource(geojson_file_path)
        geojson_layer = geojson_datasource.CreateLayer(layer_name, layer.GetSpatialRef(), layer.GetGeomType())

        # Copy fields (attributes)
        geojson_layer.CreateFields(layer.schema)

        # Copy features, skipping features without geometry
        for feature in layer:
            if feature.GetGeometryRef() is not None:
                geojson_layer.CreateFeature(feature.Clone())

        geojson_datasource = None  # Close the GeoJSON file

        print(f"Saved {geojson_file_path} to files")

        # Perform simplification after saving the GeoJSON
        simplified_geojson_file_path = geojson_file_path.replace('.geojson', '_simplified.geojson')
        simplify_geojson(geojson_file_path, simplified_geojson_file_path, simplify_tolerance)

        print(f"Saved simplified {simplified_geojson_file_path} to files")

    datasource = None  # Close the KMZ file

    # Return the path of the first simplified GeoJSON file
    return simplified_geojson_file_path

def simplify_geojson(input_geojson, output_geojson, tolerance):
    """Use ogr2ogr to simplify a GeoJSON file."""
    try:
        subprocess.run([
            'ogr2ogr',
            '-f', 'GeoJSON',
            output_geojson,
            input_geojson,
            '-simplify', str(tolerance)
        ], check=True)
        print(f"Simplified {input_geojson} to {output_geojson} with tolerance {tolerance}")
    except subprocess.CalledProcessError as e:
        print(f"Error simplifying {input_geojson}: {e}")

def convert_geojson_to_vector_tiles(geojson_file_path, output_tile_dir, min_zoom=6, max_zoom=10):
    """Convert GeoJSON to vector tiles using Tippecanoe."""
    
    # Check for the simplified GeoJSON file
    simplified_geojson_file_path = geojson_file_path.replace('.geojson', '_simplified.geojson')
    geojson_file_to_use = simplified_geojson_file_path if os.path.exists(simplified_geojson_file_path) else geojson_file_path

    os.makedirs(output_tile_dir, exist_ok=True)
    tile_output = os.path.join(output_tile_dir, 'tiles.mbtiles')

    # Generate vector tiles using Tippecanoe with customized settings for better compatibility
    subprocess.run([
        'tippecanoe',
        '-o', tile_output,
        '--maximum-zoom', str(max_zoom),
        '--minimum-zoom', str(min_zoom),
        '--no-tile-compression',  # Avoid compressing tiles for easier compatibility
        '--drop-densest-as-needed',  # Reduce complexity of dense tiles
        '--force',  # Overwrite existing tiles
        geojson_file_to_use
    ], check=True)

    # Extract the tiles from the mbtiles file
    subprocess.run([
        'tile-join',
        '-e', output_tile_dir,
        '--force',  # Force overwrite
        tile_output
    ], check=True)

    print(f"Vector tiles saved in {output_tile_dir}")

# Main driver function
def driver():
    kmz_file_path = os.path.join(output_directory, "ownership.kmz")
    geojson_file_base = "ownership"

    # Step 1: Download KMZ
    print(f"Downloading {kmz_url}...")
    download_file(kmz_url, kmz_file_path)

    # Step 2: Convert KMZ to GeoJSON
    print(f"Converting KMZ to GeoJSON...")
    geojson_file_path = convert_kmz_to_geojson(kmz_file_path, geojson_file_base)

    if geojson_file_path is None:
        print("No valid GeoJSON file found.")
        return

    # Step 3: Convert GeoJSON to vector tiles
    tile_output_directory = os.path.join(output_directory, "ownership_tiles")
    print(f"Converting GeoJSON to vector tiles...")
    convert_geojson_to_vector_tiles("test_square.geojson", "ownership_tile_dir/tile_dir/ownership_tiles")

# Run the process
driver()
print("Process completed.")
