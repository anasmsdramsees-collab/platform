"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import type { Locale } from "@/lib/i18n/config";
import {
  type ClimateKind,
  type PropertyDef,
  type RoomDef,
  type SystemKey,
  roomName,
} from "@/lib/builder-data";
import {
  CeilingLight,
  CeilingSpeaker,
  CentralVent,
  Curtains,
  DomeCamera,
  DoorLock,
  GasSensor,
  HealthPuck,
  MotionSensor,
  SplitAc,
} from "./fixtures";

const LEVEL_HEIGHT = 2.9;
const WALL = 0.12;

interface RoomProps {
  room: RoomDef;
  locale: Locale;
  selected: boolean;
  chosen: SystemKey[];
  climate: ClimateKind;
  brightness: number;
  curtainsOpen: boolean;
  locked: boolean;
  acOn: boolean;
  onSelect: () => void;
}

/** Places the window wall for a room so curtains hang on the right side. */
function windowTransform(room: RoomDef): { position: [number, number, number]; rotation: [number, number, number]; width: number } | null {
  if (!room.window) return null;
  const [w, d] = room.size;
  switch (room.window) {
    case "north":
      return { position: [0, 0, -d / 2 + 0.09], rotation: [0, 0, 0], width: w * 0.72 };
    case "south":
      return { position: [0, 0, d / 2 - 0.09], rotation: [0, Math.PI, 0], width: w * 0.72 };
    case "west":
      return { position: [-w / 2 + 0.09, 0, 0], rotation: [0, Math.PI / 2, 0], width: d * 0.72 };
    default:
      return { position: [w / 2 - 0.09, 0, 0], rotation: [0, -Math.PI / 2, 0], width: d * 0.72 };
  }
}

function Room({
  room,
  locale,
  selected,
  chosen,
  climate,
  brightness,
  curtainsOpen,
  locked,
  acOn,
  onSelect,
}: RoomProps) {
  const [cx, cz] = room.centre;
  const [w, d] = room.size;
  const y = room.level * LEVEL_HEIGHT;

  const has = (k: SystemKey) => chosen.includes(k) && room.systems.includes(k);
  const lit = has("lighting") ? brightness : 0;
  const window = windowTransform(room);

  return (
    <group position={[cx, y, cz]}>
      {/* A thin bright rim under the slab separates the levels visually */}
      <mesh position={[0, -0.02, 0]}>
        <boxGeometry args={[w + 0.06, 0.04, d + 0.06]} />
        <meshStandardMaterial
          color="#4c8dff"
          emissive="#4c8dff"
          emissiveIntensity={selected ? 1.1 : 0.35}
          toneMapped={false}
        />
      </mesh>

      {/* Floor slab, doubles as the click target for the room */}
      <mesh
        position={[0, 0.05, 0]}
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "auto";
        }}
      >
        <boxGeometry args={[w, 0.1, d]} />
        <meshStandardMaterial
          color={selected ? "#2b3b5c" : "#252b36"}
          roughness={0.7}
          emissive={lit > 0 ? "#3a2c10" : "#000000"}
          emissiveIntensity={lit * 0.8}
        />
      </mesh>

      {/* Two low walls only, so the interior stays readable from above */}
      <mesh position={[0, 0.7, -d / 2]}>
        <boxGeometry args={[w, 1.3, WALL]} />
        <meshStandardMaterial color="#39414f" roughness={0.8} />
      </mesh>
      <mesh position={[-w / 2, 0.7, 0]}>
        <boxGeometry args={[WALL, 1.3, d]} />
        <meshStandardMaterial color="#39414f" roughness={0.8} />
      </mesh>

      {has("lighting") && <CeilingLight position={[0, 1.75, 0]} brightness={lit} />}

      {has("curtains") && window && (
        <Curtains
          position={window.position}
          rotation={window.rotation}
          width={window.width}
          open={curtainsOpen}
        />
      )}

      {has("climate") &&
        (climate === "central" ? (
          <CentralVent position={[w / 4, 1.62, -d / 4]} running={acOn} />
        ) : (
          <SplitAc position={[0, 1.18, -d / 2 + 0.14]} rotation={[0, 0, 0]} running={acOn} />
        ))}

      {has("cameras") && <DomeCamera position={[-w / 4, 1.62, d / 4]} live />}
      {has("motion") && <MotionSensor position={[w / 2 - 0.3, 1.5, -d / 2 + 0.3]} armed />}
      {has("gas") && (
        <GasSensor position={[-w / 2 + 0.16, 0.95, d / 4]} rotation={[0, Math.PI / 2, 0]} armed />
      )}
      {has("health") && <HealthPuck position={[-w / 4, 0.14, d / 4]} active />}
      {has("audio") && (
        <>
          <CeilingSpeaker position={[-w / 4, 1.66, -d / 4]} />
          <CeilingSpeaker position={[w / 4, 1.66, d / 4]} />
        </>
      )}
      {has("security") && (
        <DoorLock position={[w / 2 - 0.1, 0.85, 0]} rotation={[0, -Math.PI / 2, 0]} locked={locked} />
      )}

      {selected && (
        <Html center position={[0, 2.35, 0]} distanceFactor={14} zIndexRange={[20, 0]}>
          <span className="whitespace-nowrap rounded-full border border-white/15 bg-black/80 px-3 py-1 text-[11px] text-white backdrop-blur-sm">
            {roomName(room, locale)}
          </span>
        </Html>
      )}
    </group>
  );
}

export function BuilderScene({
  property,
  locale,
  chosen,
  brightness,
  curtainsOpen,
  locked,
  acOn,
  selectedRoom,
  onSelectRoom,
}: {
  property: PropertyDef;
  locale: Locale;
  chosen: SystemKey[];
  brightness: number;
  curtainsOpen: boolean;
  locked: boolean;
  acOn: boolean;
  selectedRoom: string | null;
  onSelectRoom: (id: string | null) => void;
}) {
  const lightsOn = brightness > 0.02;
  // Frame the camera around the building's footprint.
  const radius = useMemo(() => {
    const maxX = Math.max(...property.rooms.map((r) => Math.abs(r.centre[0]) + r.size[0] / 2));
    const maxZ = Math.max(...property.rooms.map((r) => Math.abs(r.centre[1]) + r.size[1] / 2));
    return Math.max(maxX, maxZ) * 2.8;
  }, [property]);

  return (
    <Canvas
      shadows={false}
      dpr={[1, 1.75]}
      camera={{ position: [radius * 0.95, radius * 0.85, radius * 0.95], fov: 42 }}
      onPointerMissed={() => onSelectRoom(null)}
      style={{ touchAction: "none" }}
    >
      <color attach="background" args={["#0e1016"]} />
      <fog attach="fog" args={["#0b0c0e", radius * 1.6, radius * 3.4]} />

      <ambientLight intensity={0.62 + brightness * 0.35} />
      <directionalLight position={[6, 14, 8]} intensity={1.35 + brightness * 0.5} color="#dce6ff" />
      <directionalLight position={[-9, 7, -6]} intensity={0.8} color="#4c8dff" />
      <hemisphereLight args={["#7f9dd6", "#0d1016", 0.7]} />

      {/* Ground pad */}
      <RoundedBox args={[radius * 1.9, 0.3, radius * 1.9]} radius={0.12} position={[0, -0.2, 0]}>
        <meshStandardMaterial color="#171b23" roughness={1} />
      </RoundedBox>

      {property.rooms.map((room) => (
        <Room
          key={`${room.level}-${room.id}`}
          room={room}
          locale={locale}
          selected={selectedRoom === `${room.level}-${room.id}`}
          chosen={chosen}
          climate={property.climate}
          brightness={brightness}
          curtainsOpen={curtainsOpen}
          locked={locked}
          acOn={acOn}
          onSelect={() => onSelectRoom(`${room.level}-${room.id}`)}
        />
      ))}

      <OrbitControls
        makeDefault
        enablePan={false}
        minPolarAngle={0.25}
        maxPolarAngle={Math.PI / 2.35}
        minDistance={radius * 0.7}
        maxDistance={radius * 2.1}
        autoRotate={!selectedRoom}
        autoRotateSpeed={0.5}
      />
    </Canvas>
  );
}
