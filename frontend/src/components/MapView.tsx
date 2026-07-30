import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef, useState } from "react";
import { useStore } from "../store";
import { createArrowIcon } from "./mapIcons";
import GeofenceDrawTool from "./GeofenceDrawTool";

const MAP_STYLE_URL =
  import.meta.env.VITE_MAP_STYLE_URL ?? "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

// Center of the default simulator bounding box (downtown San Francisco).
const DEFAULT_CENTER: [number, number] = [-122.4127, 37.7749];

function vehiclesToGeoJSON(vehicles: Map<number, { id: number; name: string; color: string; lat: number; lon: number; heading_degrees: number; speed_kmh: number }>) {
  return {
    type: "FeatureCollection" as const,
    features: [...vehicles.values()].map((v) => ({
      type: "Feature" as const,
      geometry: { type: "Point" as const, coordinates: [v.lon, v.lat] },
      properties: { id: v.id, name: v.name, color: v.color, heading_degrees: v.heading_degrees, speed_kmh: v.speed_kmh },
    })),
  };
}

function geofencesToGeoJSON(geofences: Map<number, { id: number; name: string; color: string; coordinates: [number, number][] }>) {
  return {
    type: "FeatureCollection" as const,
    features: [...geofences.values()].map((g) => ({
      type: "Feature" as const,
      geometry: { type: "Polygon" as const, coordinates: [g.coordinates] },
      properties: { id: g.id, name: g.name, color: g.color },
    })),
  };
}

export default function MapView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [map, setMap] = useState<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE_URL,
      center: DEFAULT_CENTER,
      zoom: 13,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");

    map.on("load", () => {
      const icon = createArrowIcon(32);
      map.addImage("vehicle-arrow", icon, { sdf: true });

      map.addSource("vehicles", { type: "geojson", data: vehiclesToGeoJSON(new Map()) });
      map.addSource("geofences", { type: "geojson", data: geofencesToGeoJSON(new Map()) });

      map.addLayer({
        id: "geofences-fill",
        type: "fill",
        source: "geofences",
        paint: { "fill-color": ["get", "color"], "fill-opacity": 0.15 },
      });
      map.addLayer({
        id: "geofences-outline",
        type: "line",
        source: "geofences",
        paint: { "line-color": ["get", "color"], "line-width": 2 },
      });

      map.addLayer({
        id: "vehicles-symbol",
        type: "symbol",
        source: "vehicles",
        layout: {
          "icon-image": "vehicle-arrow",
          "icon-rotate": ["get", "heading_degrees"],
          "icon-rotation-alignment": "map",
          "icon-size": 0.6,
          "icon-allow-overlap": true,
          "text-field": ["get", "name"],
          "text-offset": [0, 1.5],
          "text-size": 11,
          "text-allow-overlap": true,
        },
        paint: {
          "icon-color": ["get", "color"],
          "text-color": "#e5e7eb",
          "text-halo-color": "#0b0f19",
          "text-halo-width": 1,
        },
      });

      const popup = new maplibregl.Popup({ closeButton: false, offset: 16 });
      map.on("mouseenter", "vehicles-symbol", (e) => {
        map.getCanvas().style.cursor = "pointer";
        const f = e.features?.[0];
        if (!f) return;
        const p = f.properties as { name: string; speed_kmh: number };
        popup
          .setLngLat((f.geometry as GeoJSON.Point).coordinates as [number, number])
          .setHTML(`<strong>${p.name}</strong><br/>${Math.round(p.speed_kmh)} km/h`)
          .addTo(map);
      });
      map.on("mouseleave", "vehicles-symbol", () => {
        map.getCanvas().style.cursor = "";
        popup.remove();
      });
      map.on("click", "vehicles-symbol", (e) => {
        const f = e.features?.[0];
        if (!f) return;
        useStore.getState().selectVehicle(f.properties!.id as number);
      });

      setMap(map);
      setMapReady(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Push live vehicle positions into the map source on every store update.
  useEffect(() => {
    if (!mapReady) return;
    const unsubscribe = useStore.subscribe((state) => {
      const source = mapRef.current?.getSource("vehicles") as maplibregl.GeoJSONSource | undefined;
      source?.setData(vehiclesToGeoJSON(state.vehicles) as never);
    });
    // apply once immediately
    const source = mapRef.current?.getSource("vehicles") as maplibregl.GeoJSONSource | undefined;
    source?.setData(vehiclesToGeoJSON(useStore.getState().vehicles) as never);
    return unsubscribe;
  }, [mapReady]);

  useEffect(() => {
    if (!mapReady) return;
    const unsubscribe = useStore.subscribe((state) => {
      const source = mapRef.current?.getSource("geofences") as maplibregl.GeoJSONSource | undefined;
      source?.setData(geofencesToGeoJSON(state.geofences) as never);
    });
    const source = mapRef.current?.getSource("geofences") as maplibregl.GeoJSONSource | undefined;
    source?.setData(geofencesToGeoJSON(useStore.getState().geofences) as never);
    return unsubscribe;
  }, [mapReady]);

  // Fly to a vehicle when selected from the sidebar.
  useEffect(() => {
    return useStore.subscribe((state, prevState) => {
      if (state.selectedVehicleId === null || state.selectedVehicleId === prevState.selectedVehicleId) return;
      const vehicle = state.vehicles.get(state.selectedVehicleId);
      if (vehicle && mapRef.current) {
        mapRef.current.flyTo({ center: [vehicle.lon, vehicle.lat], zoom: 15, speed: 1.2 });
      }
    });
  }, []);

  return (
    <div className="map-container" ref={containerRef}>
      {mapReady && map && <GeofenceDrawTool map={map} />}
    </div>
  );
}
