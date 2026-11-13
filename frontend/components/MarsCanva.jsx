'use client';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Box, Cylinder } from '@react-three/drei';
import { useRef } from 'react';
import * as THREE from 'three';

function ColonyTerrain() {
  return (
    <group>
      {/* Martian Ground Plane */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.5, 0]}>
        <planeGeometry args={[30, 30, 32, 32]} />
        <meshStandardMaterial color="#8b3a2b" roughness={0.9} metalness={0.1} />
      </mesh>

      {/* Central Habitat Dome */}
      <group position={[0, -0.5, 0]}>
        {/* Dome Structure */}
        <Sphere args={[1.2, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2]}>
          <meshStandardMaterial color="#e2e8f0" roughness={0.3} metalness={0.8} transparent opacity={0.85} />
        </Sphere>
        {/* Habitat Base Cylinder */}
        <Cylinder args={[1.2, 1.2, 0.4, 32]} position={[0, -0.2, 0]}>
          <meshStandardMaterial color="#334155" roughness={0.5} />
        </Cylinder>
      </group>

      {/* Secondary Outpost Dome */}
      <group position={[2.5, -0.8, -1.5]} scale={[0.6, 0.6, 0.6]}>
        <Sphere args={[1.2, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2]}>
          <meshStandardMaterial color="#38bdf8" roughness={0.3} metalness={0.9} transparent opacity={0.8} />
        </Sphere>
        <Cylinder args={[1.2, 1.2, 0.4, 32]} position={[0, -0.2, 0]}>
          <meshStandardMaterial color="#1e293b" roughness={0.5} />
        </Cylinder>
      </group>
    </group>
  );
}

function OrbitingRover() {
  const roverRef = useRef();

  // Animate the rover moving in an ellipse around the colony
  useFrame(({ clock }) => {
    const elapsedTime = clock.getElapsedTime() * 0.4;
    const x = Math.cos(elapsedTime) * 3.5;
    const z = Math.sin(elapsedTime) * 2.5;
    roverRef.current.position.x = x;
    roverRef.current.position.z = z;
    roverRef.current.rotation.y = -elapsedTime;
  });

  return (
    <group ref={roverRef} position={[3.5, -1.3, 0]} scale={[0.4, 0.4, 0.4]}>
      {/* Rover Chassis */}
      <Box args={[2, 0.8, 3]}>
        <meshStandardMaterial color="#f97316" roughness={0.4} metalness={0.6} />
      </Box>
      {/* Solar Panel Array on Top */}
      <Box args={[1.8, 0.1, 2]} position={[0, 0.5, 0]}>
        <meshStandardMaterial color="#1e3a8a" roughness={0.2} metalness={0.8} />
      </Box>
    </group>
  );
}

export default function MarsCanvas() {
  return (
    <div className="w-full h-[450px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative">
      <Canvas camera={{ position: [0, 3, 7], fov: 50 }}>
        {/* Martian Atmospheric Lighting */}
        <ambientLight intensity={0.4} color="#ffd8b8" />
        <directionalLight position={[10, 20, 10]} intensity={1.8} color="#ffedd5" />
        <pointLight position={[-5, 2, -5]} intensity={0.5} color="#ea580c" />

        <ColonyTerrain />
        <OrbitingRover />

        <OrbitControls 
          enableZoom={true} 
          maxPolarAngle={Math.PI / 2 - 0.05} // Prevent camera from going below ground
          minDistance={3}
          maxDistance={12}
        />
      </Canvas>
      <div className="absolute bottom-3 left-4 text-xs font-mono text-slate-400 pointer-events-none bg-slate-900/90 px-3 py-1.5 rounded border border-slate-800">
        VISUALIZATION: ARCADIA PLANITIA SURFACE SECTOR 1
      </div>
    </div>
  );
}