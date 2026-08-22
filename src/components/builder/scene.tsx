"use client";

import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import type { Locale } from "@/lib/i18n/config";
import {
  type PropertyDef,
  type RoomDef,
  type SystemKey,
  SYSTEMS,
  roomName,
} from "@/lib/builder-data";

const LEVEL_HEIGHT = 2.9;
const WALL = 0.12;

/** A soft pulse so active device markers read as "live" without being noisy. */
function Marker({
  position,
  color,
  active,
}: {
  position: [number, number, number];
  color: string;
  active: boolean;
}) {
  const ref = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    const s = active ? 1 + Math.sin(t * 2.4) * 0.12 : 1;
    ref.current.scale.setScalar(s);
  });
  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[0.16, 20, 20]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={active ? 1.6 : 0.15}
        toneMapped={false}
      />
    </mesh>
  );
}

function Room({
  room,
  locale,
  selected,
  chosen,
  lightsOn,
  onSelect,
}: {
  room: RoomDef;
  locale: Locale;
  selected: boolean;
  chosen: SystemKey[];
  lightsOn: boolean;
  onSelect: () => void;
}) {
  const [cx, cz] = room.centre;
  const [w, d] = room.size;
  const y = room.level * LEVEL_HEIGHT;

  const active = chosen.filter((s) => room.systems.includes(s));
  const glow = lightsOn && active.includes("lighting");

  return (
    <group position={[cx, y, cz]}>
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
          emissive={glow ? "#3a2c10" : "#000000"}
          emissiveIntensity={glow ? 0.7 : 0}
        />
      </mesh>

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

      {/* Two low walls only, so the interior stays readable from above */}
      <mesh position={[0, 0.7, -d / 2]}>
        <boxGeometry args={[w, 1.3, WALL]} />
        <meshStandardMaterial color="#39414f" roughness={0.8} />
      </mesh>
      <mesh position={[-w / 2, 0.7, 0]}>
        <boxGeometry args={[WALL, 1.3, d]} />
        <meshStandardMaterial color="#39414f" roughness={0.8} />
      </mesh>

      {/* A warm pool of light when the room's lighting is switched on */}
      {glow && <pointLight position={[0, 1.6, 0]} intensity={5} distance={5.5} color="#ffd9a0" />}

      {/* Device markers, spread along the room so they never stack */}
      {active.map((key, i) => {
        const system = SYSTEMS.find((s) => s.key === key)!;
        const step = w / (active.length + 1);
        return (
          <Marker
            key={key}
            position={[-w / 2 + step * (i + 1), 1.25, 0]}
            color={system.color}
            active={lightsOn || key !== "lighting"}
          />
        );
      })}

      {selected && (
        <Html center position={[0, 2.1, 0]} distanceFactor={14} zIndexRange={[20, 0]}>
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
  lightsOn,
  selectedRoom,
  onSelectRoom,
}: {
  property: PropertyDef;
  locale: Locale;
  chosen: SystemKey[];
  lightsOn: boolean;
  selectedRoom: string | null;
  onSelectRoom: (id: string | null) => void;
}) {
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

      <ambientLight intensity={lightsOn ? 1.15 : 0.75} />
      <directionalLight position={[6, 14, 8]} intensity={lightsOn ? 1.9 : 1.4} color="#dce6ff" />
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
          lightsOn={lightsOn}
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
