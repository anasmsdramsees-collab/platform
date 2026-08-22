"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/**
 * A pendant fixture: brass rod, shade, and a glowing diffuser whose brightness
 * follows the dimmer. Reads as a real light, not a marker dot.
 */
export function CeilingLight({
  position,
  brightness,
}: {
  position: [number, number, number];
  brightness: number; // 0..1
}) {
  const diffuser = useRef<THREE.MeshStandardMaterial>(null);
  const lamp = useRef<THREE.PointLight>(null);

  useFrame((_, delta) => {
    const k = Math.min(1, delta * 6);
    if (diffuser.current) {
      diffuser.current.emissiveIntensity = lerp(
        diffuser.current.emissiveIntensity,
        brightness * 3.2,
        k
      );
    }
    if (lamp.current) {
      lamp.current.intensity = lerp(lamp.current.intensity, brightness * 9, k);
    }
  });

  return (
    <group position={position}>
      {/* Drop rod */}
      <mesh position={[0, 0.36, 0]}>
        <cylinderGeometry args={[0.015, 0.015, 0.72, 8]} />
        <meshStandardMaterial color="#8b7a5e" metalness={0.9} roughness={0.35} />
      </mesh>
      {/* Shade */}
      <mesh>
        <coneGeometry args={[0.22, 0.2, 24, 1, true]} />
        <meshStandardMaterial
          color="#c8b48a"
          metalness={0.85}
          roughness={0.28}
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* Glowing diffuser */}
      <mesh position={[0, -0.09, 0]}>
        <sphereGeometry args={[0.11, 20, 16]} />
        <meshStandardMaterial
          ref={diffuser}
          color="#fff3dc"
          emissive="#ffcf8a"
          emissiveIntensity={0}
          toneMapped={false}
        />
      </mesh>
      <pointLight ref={lamp} position={[0, -0.2, 0]} intensity={0} distance={5.5} color="#ffd9a3" decay={2} />
    </group>
  );
}

/** Fabric curtain panels on a rail; they part when open and meet when closed. */
export function Curtains({
  position,
  rotation,
  width,
  open,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
  width: number;
  open: boolean;
}) {
  const left = useRef<THREE.Group>(null);
  const right = useRef<THREE.Group>(null);
  const panel = width / 2;

  useFrame((_, delta) => {
    const k = Math.min(1, delta * 5);
    // Open pulls each panel out to the jamb; closed brings them together.
    const target = open ? panel * 0.32 : panel * 0.98;
    if (left.current) left.current.scale.x = lerp(left.current.scale.x, target / panel, k);
    if (right.current) right.current.scale.x = lerp(right.current.scale.x, target / panel, k);
  });

  return (
    <group position={position} rotation={rotation}>
      {/* Rail */}
      <mesh position={[0, 1.28, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.022, 0.022, width, 8]} />
        <meshStandardMaterial color="#9aa3b2" metalness={0.8} roughness={0.3} />
      </mesh>

      {/* Left panel, anchored at the jamb so scaling reads as sliding fabric */}
      <group ref={left} position={[-width / 2, 0, 0]} scale={[1, 1, 1]}>
        <mesh position={[panel / 2, 0.62, 0]}>
          <boxGeometry args={[panel, 1.24, 0.05]} />
          <meshStandardMaterial color="#6c7689" roughness={0.95} />
        </mesh>
      </group>

      {/* Right panel */}
      <group ref={right} position={[width / 2, 0, 0]} scale={[1, 1, 1]}>
        <mesh position={[-panel / 2, 0.62, 0]}>
          <boxGeometry args={[panel, 1.24, 0.05]} />
          <meshStandardMaterial color="#6c7689" roughness={0.95} />
        </mesh>
      </group>
    </group>
  );
}

/** Wall-mounted mini split, the unit used in apartments and offices. */
export function SplitAc({
  position,
  rotation,
  running,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
  running: boolean;
}) {
  const led = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(({ clock }) => {
    if (led.current) {
      led.current.emissiveIntensity = running ? 1.4 + Math.sin(clock.getElapsedTime() * 2) * 0.35 : 0.1;
    }
  });

  return (
    <group position={position} rotation={rotation}>
      <mesh>
        <boxGeometry args={[0.86, 0.26, 0.2]} />
        <meshStandardMaterial color="#eef1f6" roughness={0.5} />
      </mesh>
      {/* Louvre slot */}
      <mesh position={[0, -0.1, 0.06]}>
        <boxGeometry args={[0.74, 0.05, 0.1]} />
        <meshStandardMaterial color="#aeb6c4" roughness={0.6} />
      </mesh>
      <mesh position={[0.33, 0.04, 0.105]}>
        <sphereGeometry args={[0.018, 10, 10]} />
        <meshStandardMaterial ref={led} color="#5ed4d0" emissive="#5ed4d0" emissiveIntensity={0} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** Ceiling diffuser for the villa's ducted central system. */
export function CentralVent({
  position,
  running,
}: {
  position: [number, number, number];
  running: boolean;
}) {
  const blade = useRef<THREE.Group>(null);
  useFrame((_, delta) => {
    if (blade.current && running) blade.current.rotation.y += delta * 0.5;
  });

  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[0.62, 0.05, 0.62]} />
        <meshStandardMaterial color="#dfe4ec" roughness={0.55} />
      </mesh>
      <group ref={blade} position={[0, -0.035, 0]}>
        {[0, 1, 2].map((i) => (
          <mesh key={i} position={[0, 0, -0.16 + i * 0.16]}>
            <boxGeometry args={[0.5, 0.02, 0.05]} />
            <meshStandardMaterial
              color="#9fb2c9"
              emissive={running ? "#5ed4d0" : "#000000"}
              emissiveIntensity={running ? 0.5 : 0}
            />
          </mesh>
        ))}
      </group>
    </group>
  );
}

/** Corner motion detector; the lens blinks when the system is armed. */
export function MotionSensor({
  position,
  armed,
}: {
  position: [number, number, number];
  armed: boolean;
}) {
  const lens = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(({ clock }) => {
    if (lens.current) {
      const t = clock.getElapsedTime();
      lens.current.emissiveIntensity = armed ? (Math.sin(t * 3.2) > 0.85 ? 2.4 : 0.15) : 0.05;
    }
  });

  return (
    <group position={position} rotation={[Math.PI / 5, 0, 0]}>
      <mesh>
        <cylinderGeometry args={[0.09, 0.11, 0.07, 18]} />
        <meshStandardMaterial color="#e9ecf1" roughness={0.5} />
      </mesh>
      <mesh position={[0, -0.05, 0]}>
        <sphereGeometry args={[0.06, 16, 12, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2]} />
        <meshStandardMaterial ref={lens} color="#2b3140" emissive="#ffa94d" emissiveIntensity={0} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** Gas detector on the kitchen wall, with a status ring. */
export function GasSensor({
  position,
  rotation,
  armed,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
  armed: boolean;
}) {
  return (
    <group position={position} rotation={rotation}>
      <mesh>
        <boxGeometry args={[0.24, 0.3, 0.08]} />
        <meshStandardMaterial color="#f1f3f7" roughness={0.5} />
      </mesh>
      {/* Vent grille */}
      {[0, 1, 2].map((i) => (
        <mesh key={i} position={[0, 0.05 - i * 0.05, 0.045]}>
          <boxGeometry args={[0.15, 0.015, 0.01]} />
          <meshStandardMaterial color="#b9c1cf" />
        </mesh>
      ))}
      <mesh position={[0, -0.1, 0.045]}>
        <circleGeometry args={[0.022, 16]} />
        <meshStandardMaterial
          color={armed ? "#7ee08a" : "#5a6270"}
          emissive={armed ? "#7ee08a" : "#000000"}
          emissiveIntensity={armed ? 1.6 : 0}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

/** Bedside Syltra Health puck: a quiet ring that breathes while it senses. */
export function HealthPuck({
  position,
  active,
}: {
  position: [number, number, number];
  active: boolean;
}) {
  const ring = useRef<THREE.MeshStandardMaterial>(null);
  useFrame(({ clock }) => {
    if (ring.current) {
      const t = clock.getElapsedTime();
      // A slow breath, roughly the pace of restful breathing.
      ring.current.emissiveIntensity = active ? 0.7 + Math.sin(t * 0.9) * 0.55 : 0.05;
    }
  });

  return (
    <group position={position}>
      <mesh>
        <cylinderGeometry args={[0.13, 0.15, 0.08, 24]} />
        <meshStandardMaterial color="#20242e" roughness={0.6} />
      </mesh>
      <mesh position={[0, 0.045, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.09, 0.014, 12, 32]} />
        <meshStandardMaterial ref={ring} color="#63d3a6" emissive="#63d3a6" emissiveIntensity={0} toneMapped={false} />
      </mesh>
    </group>
  );
}

/** Small dome camera on the ceiling. */
export function DomeCamera({ position, live }: { position: [number, number, number]; live: boolean }) {
  return (
    <group position={position}>
      <mesh>
        <cylinderGeometry args={[0.13, 0.13, 0.06, 20]} />
        <meshStandardMaterial color="#22262f" roughness={0.5} />
      </mesh>
      <mesh position={[0, -0.05, 0]}>
        <sphereGeometry args={[0.1, 20, 14, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2]} />
        <meshPhysicalMaterial color="#11141a" roughness={0.15} transmission={0.35} thickness={0.4} />
      </mesh>
      <mesh position={[0.075, -0.03, 0]}>
        <sphereGeometry args={[0.014, 10, 10]} />
        <meshStandardMaterial
          color="#c78bff"
          emissive="#c78bff"
          emissiveIntensity={live ? 2 : 0}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

/** Door lock plate beside the entrance. */
export function DoorLock({
  position,
  rotation,
  locked,
}: {
  position: [number, number, number];
  rotation: [number, number, number];
  locked: boolean;
}) {
  return (
    <group position={position} rotation={rotation}>
      <mesh>
        <boxGeometry args={[0.16, 0.44, 0.06]} />
        <meshStandardMaterial color="#2a2f3a" metalness={0.7} roughness={0.35} />
      </mesh>
      <mesh position={[0, 0.1, 0.035]}>
        <circleGeometry args={[0.05, 20]} />
        <meshStandardMaterial
          color={locked ? "#ff6b6b" : "#7ee08a"}
          emissive={locked ? "#ff6b6b" : "#7ee08a"}
          emissiveIntensity={1.5}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

/** Ceiling speaker disc. */
export function CeilingSpeaker({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh>
        <cylinderGeometry args={[0.16, 0.16, 0.04, 24]} />
        <meshStandardMaterial color="#e7eaf0" roughness={0.6} />
      </mesh>
      <mesh position={[0, -0.025, 0]}>
        <cylinderGeometry args={[0.115, 0.115, 0.01, 24]} />
        <meshStandardMaterial color="#8f98a8" roughness={0.9} />
      </mesh>
    </group>
  );
}
