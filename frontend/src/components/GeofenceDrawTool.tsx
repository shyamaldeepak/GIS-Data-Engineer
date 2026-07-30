import * as turf from "@turf/turf";
import type maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

const PALETTE = ["#ff3333", "#33cc99", "#ffaa00", "#8855ff", "#33aaff"];

const DRAFT_SOURCE_ID = "geofence-draft";

/**
 * Custom click-to-place-vertex polygon drawer. Deliberately avoids
 * mapbox-gl-draw, which has known version-compatibility friction with
 * MapLibre GL JS -- this is a small, dependency-light alternative built
 * directly on the MapLibre + turf.js APIs already in use elsewhere.
 */
export default function GeofenceDrawTool({ map }: { map: maplibregl.Map }) {
  const [drawing, setDrawing] = useState(false);
  const [points, setPoints] = useState<[number, number][]>([]);
  const [saving, setSaving] = useState(false);
  const pointsRef = useRef(points);
  pointsRef.current = points;

  useEffect(() => {
    if (map.getSource(DRAFT_SOURCE_ID)) return;
    map.addSource(DRAFT_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({
      id: "geofence-draft-fill",
      type: "fill",
      source: DRAFT_SOURCE_ID,
      filter: ["==", ["geometry-type"], "Polygon"],
      paint: { "fill-color": "#ff3333", "fill-opacity": 0.2 },
    });
    map.addLayer({
      id: "geofence-draft-line",
      type: "line",
      source: DRAFT_SOURCE_ID,
      filter: ["==", ["geometry-type"], "LineString"],
      paint: { "line-color": "#ff3333", "line-width": 2, "line-dasharray": [2, 1] },
    });
    map.addLayer({
      id: "geofence-draft-points",
      type: "circle",
      source: DRAFT_SOURCE_ID,
      filter: ["==", ["geometry-type"], "Point"],
      paint: { "circle-radius": 5, "circle-color": "#ffffff", "circle-stroke-color": "#ff3333", "circle-stroke-width": 2 },
    });
  }, [map]);

  const renderDraft = (pts: [number, number][]) => {
    const source = map.getSource(DRAFT_SOURCE_ID) as maplibregl.GeoJSONSource | undefined;
    if (!source) return;
    const features: GeoJSON.Feature[] = pts.map((p) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: p },
      properties: {},
    }));
    if (pts.length >= 2) {
      features.push({ type: "Feature", geometry: { type: "LineString", coordinates: pts }, properties: {} });
    }
    if (pts.length >= 3) {
      features.push({
        type: "Feature",
        geometry: { type: "Polygon", coordinates: [[...pts, pts[0]]] },
        properties: {},
      });
    }
    source.setData({ type: "FeatureCollection", features } as never);
  };

  useEffect(() => {
    if (!drawing) return;
    const handleClick = (e: maplibregl.MapMouseEvent) => {
      const next: [number, number][] = [...pointsRef.current, [e.lngLat.lng, e.lngLat.lat]];
      setPoints(next);
      renderDraft(next);
    };
    map.on("click", handleClick);
    map.getCanvas().style.cursor = "crosshair";
    return () => {
      map.off("click", handleClick);
      map.getCanvas().style.cursor = "";
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [drawing, map]);

  const startDrawing = () => {
    setPoints([]);
    renderDraft([]);
    setDrawing(true);
  };

  const cancelDrawing = () => {
    setDrawing(false);
    setPoints([]);
    renderDraft([]);
  };

  const finishDrawing = async () => {
    if (points.length < 3) return;
    const ring = [...points, points[0]];
    const polygon = turf.polygon([ring]);
    const kinks = turf.kinks(polygon);
    if (kinks.features.length > 0) {
      window.alert("This shape crosses itself - try drawing a simple (non self-intersecting) polygon.");
      return;
    }

    const name = window.prompt("Name this geofence:", `Zone ${Date.now().toString().slice(-4)}`);
    if (!name) return;

    setSaving(true);
    try {
      const color = PALETTE[Math.floor(Math.random() * PALETTE.length)];
      await api.createGeofence({ name, color, coordinates: ring });
      cancelDrawing();
    } catch (err) {
      window.alert(`Could not save geofence: ${(err as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="draw-toolbar">
      {!drawing ? (
        <button className="btn btn-primary" onClick={startDrawing}>
          + Draw geofence
        </button>
      ) : (
        <>
          <span className="draw-hint">Click the map to add points ({points.length} placed)</span>
          <button className="btn btn-success" disabled={points.length < 3 || saving} onClick={finishDrawing}>
            {saving ? "Saving..." : "Finish"}
          </button>
          <button className="btn btn-ghost" onClick={cancelDrawing}>
            Cancel
          </button>
        </>
      )}
    </div>
  );
}
