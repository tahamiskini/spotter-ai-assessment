import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from 'react-leaflet';

import { TripRoute } from '@/types/api';

import { STOP_META } from '../utils';

const stopIcon = (color: string) =>
  L.divIcon({
    className: 'hos-stop-marker',
    html: `<span style="
      display:block;width:16px;height:16px;border-radius:9999px;
      background:${color};border:2px solid #fff;
      box-shadow:0 0 0 1px rgba(0,0,0,0.25);"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

const FitBounds = ({ points }: { points: [number, number][] }) => {
  const map = useMap();
  useEffect(() => {
    if (points.length > 0) {
      map.fitBounds(points, { padding: [32, 32] });
    }
  }, [map, points]);
  return null;
};

type RouteMapProps = {
  route: TripRoute;
};

export const RouteMap = ({ route }: RouteMapProps) => {
  const points = route.geometry;
  const center = points[Math.floor(points.length / 2)] ?? [39.5, -98.35];

  return (
    <div className="h-full min-h-90 w-full overflow-hidden rounded-lg border">
      <MapContainer
        center={center}
        zoom={5}
        scrollWheelZoom
        className="h-full w-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {points.length > 1 && (
          <Polyline positions={points} color="#2563eb" weight={4} opacity={0.8} />
        )}
        {route.stops.map((stop, i) => (
          <Marker
            key={`${stop.type}-${i}`}
            position={[stop.lat, stop.lng]}
            icon={stopIcon(STOP_META[stop.type].color)}
          >
            <Popup>
              <div className="text-sm">
                <div className="font-semibold">{STOP_META[stop.type].label}</div>
                <div>{stop.label}</div>
              </div>
            </Popup>
          </Marker>
        ))}
        <FitBounds points={points} />
      </MapContainer>
    </div>
  );
};
