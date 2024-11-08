import React, { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Set your Mapbox access token
mapboxgl.accessToken = 'pk.eyJ1Ijoibm9haC1nYW5zIiwiYSI6ImNsb255ajJteDB5Z2gya3BpdXU5M29oY3YifQ.VbPKEHZ91PNoSAH-raskhw';

function App() {
  const mapContainerRef = useRef(null);

  useEffect(() => {
    // Initialize the Mapbox map
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v11', // You can change this style URL
      center: [-110.76, 43.5], // Center coordinates [lng, lat]
      zoom: 9, // Starting zoom level
    });

    // Add zoom and rotation controls to the map
    map.addControl(new mapboxgl.NavigationControl());

    // Log zoom level to the console whenever the zoom changes
    map.on('zoom', () => {
      console.log(`Current zoom level: ${map.getZoom()}`);
    });

    // Add vector tile source from your Google Cloud bucket
    map.on('load', () => {
      map.addSource('ownership', {
        type: 'vector',
        tiles: [
          'https://storage.googleapis.com/first_bucket_store/Tiles/Test/{z}/{x}/{y}.pbf'
        ],
        minzoom: 6, // Adjust min zoom level as needed
        maxzoom: 14 // Adjust max zoom level as needed
      });

      // Add a layer to display vector tiles
      map.addLayer({
        id: 'ownership-layer',
        type: 'fill',
        source: 'ownership',
        'source-layer': 'ownership_ownership', // Adjust this if your tiles have a different layer name
        paint: {
          'fill-color': '#AAAAAA',
          'fill-opacity': 0.3,
          'fill-outline-color': '#000000',
          'line-width': 10
        }
      });

      // Click event handler
      map.on('click', 'ownership-layer', (e) => {
        if (e.features.length > 0) {
          const feature = e.features[0];
          let coordinates;
      
          // Check if feature is a Point or use the first coordinate for polygons/lines
          if (feature.geometry.type === 'Point') {
            coordinates = feature.geometry.coordinates.slice();
          } else if (feature.geometry.type === 'Polygon') {
            // For polygons, use the first coordinate of the first ring as an example
            coordinates = feature.geometry.coordinates[0][0].slice();
          } else if (feature.geometry.type === 'MultiPolygon') {
            // For multipolygons, use the first coordinate of the first polygon's first ring
            coordinates = feature.geometry.coordinates[0][0][0].slice();
          } else {
            console.warn('Unhandled geometry type:', feature.geometry.type);
            return;
          }
      
          const properties = feature.properties;
      
          // Ensure longitude is between -180 and 180 degrees
          while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
          }
      
          // Create a popup with feature properties
          new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(
              `<div>${Object.entries(properties)
                .map(([key, value]) => `<strong>${key}</strong>: ${value}`)
                .join('<br>')}</div>`
            )
            .addTo(map);
        }
      });
      

      // Change the cursor to a pointer when the mouse is over the layer
      map.on('mouseenter', 'ownership-layer', () => {
        map.getCanvas().style.cursor = 'pointer';
      });

      // Change it back to default when it leaves
      map.on('mouseleave', 'ownership-layer', () => {
        map.getCanvas().style.cursor = '';
      });
    });

    // Clean up on unmount
    return () => map.remove();
  }, []);

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <div ref={mapContainerRef} style={{ height: '100%', width: '100%' }}></div>
    </div>
  );
}

export default App;
