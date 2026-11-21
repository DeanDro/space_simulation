'use client';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere } from '@react-three/drei';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';

const MARS_RADIUS = 2;
const MAX_BEACONS = 36;
const CREW_PER_LIGHT = 100;

function latLonToVector3(lat, lon, radius) {
  const phi = THREE.MathUtils.degToRad(90 - lat);
  const theta = THREE.MathUtils.degToRad(lon + 180);

  const x = -radius * Math.sin(phi) * Math.cos(theta);
  const z = radius * Math.sin(phi) * Math.sin(theta);
  const y = radius * Math.cos(phi);

  return [x, y, z];
}

function generateSurfaceCoordinates(count, radius) {
  const coords = [];
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));

  for (let i = 0; i < count; i++) {
    if (i === 0) {
      coords.push(latLonToVector3(46.7, -176.0, radius));
      continue;
    }

    const yRatio = 1 - (i / (count - 1)) * 1.6;
    const clampedY = Math.max(-0.85, Math.min(0.85, yRatio));
    const lat = THREE.MathUtils.radToDeg(Math.asin(clampedY));
    const lon = THREE.MathUtils.radToDeg((goldenAngle * i) % (Math.PI * 2)) - 180;

    coords.push(latLonToVector3(lat, lon, radius));
  }

  return coords;
}

function ColonyBeacon({ position, isPrimary, pulseOffset }) {
  const dotRef = useRef();
  const phaseRef = useRef(pulseOffset);
  const normal = useMemo(() => new THREE.Vector3(...position).normalize(), [position]);
  const quaternion = useMemo(() => {
    const q = new THREE.Quaternion();
    q.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
    return q;
  }, [normal]);

  useFrame((_, delta) => {
    phaseRef.current += delta * 2.0;
    if (dotRef.current) {
      const twinkle = 1 + Math.sin(phaseRef.current) * 0.12;
      dotRef.current.scale.setScalar(twinkle);
    }
  });

  return (
    <group position={position} quaternion={quaternion}>
      {/* Sharp white orbital dot oriented tangent to the Mars surface */}
      <mesh ref={dotRef}>
        <circleGeometry args={[isPrimary ? 0.018 : 0.012, 16]} />
        <meshBasicMaterial color="#ffffff" />
      </mesh>
    </group>
  );
}

function MarsPlanetWithLights({ population = 0, surfaceTextureUrl = null }) {
  const planetGroupRef = useRef();
  const [surfaceTexture, setSurfaceTexture] = useState(null);

  useEffect(() => {
    if (!surfaceTextureUrl) {
      setSurfaceTexture((prev) => {
        if (prev) prev.dispose();
        return null;
      });
      return;
    }

    const loader = new THREE.TextureLoader();
    let activeTexture = null;

    loader.load(surfaceTextureUrl, (loadedTex) => {
      loadedTex.colorSpace = THREE.SRGBColorSpace;
      loadedTex.wrapS = THREE.RepeatWrapping;
      loadedTex.wrapT = THREE.ClampToEdgeWrapping;
      loadedTex.needsUpdate = true;

      activeTexture = loadedTex;
      setSurfaceTexture((prev) => {
        if (prev) prev.dispose();
        return loadedTex;
      });
    });

    return () => {
      if (activeTexture) {
        activeTexture.dispose();
      }
    };
  }, [surfaceTextureUrl]);

  const beaconPositions = useMemo(
    () => generateSurfaceCoordinates(MAX_BEACONS, MARS_RADIUS + 0.015),
    []
  );

  const activeBeaconCount = useMemo(() => {
    const scaled = Math.floor(Math.max(0, population) / CREW_PER_LIGHT) + 1;
    return Math.min(MAX_BEACONS, Math.max(1, scaled));
  }, [population]);

  useFrame((_, delta) => {
    if (planetGroupRef.current) {
      planetGroupRef.current.rotation.y += delta * 0.08;
    }
  });

  return (
    <group ref={planetGroupRef}>
      {/* Mars Globe with Optional Uploaded Surface Image */}
      <Sphere args={[MARS_RADIUS, 48, 48]}>
        <meshStandardMaterial
          map={surfaceTexture || null}
          color={surfaceTexture ? '#ffffff' : '#b84322'}
          roughness={0.85}
          metalness={0.08}
        />
      </Sphere>

      {/* Colony & Outpost Lights */}
      {beaconPositions.slice(0, activeBeaconCount).map((pos, index) => (
        <ColonyBeacon
          key={index}
          position={pos}
          isPrimary={index === 0}
          pulseOffset={index * 0.7}
        />
      ))}
    </group>
  );
}

export default function MarsCanvas({ population = 0 }) {
  const [imageUrl, setImageUrl] = useState(null);
  const [fileName, setFileName] = useState('');
  const fileInputRef = useRef(null);

  const activeTextureUrl = imageUrl || '/mars-surface.jpg';

  const activeBeaconCount = Math.min(
    MAX_BEACONS,
    Math.max(1, Math.floor(Math.max(0, population) / CREW_PER_LIGHT) + 1)
  );

  useEffect(() => {
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [imageUrl]);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
    }

    const objectUrl = URL.createObjectURL(file);
    setImageUrl(objectUrl);
    setFileName(file.name);
  };

  const handleResetTexture = () => {
    if (imageUrl) {
      URL.revokeObjectURL(imageUrl);
    }
    setImageUrl(null);
    setFileName('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full h-[450px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative">
      {/* Top-Left Texture Upload Controls */}
      <div className="absolute top-3 left-4 z-10 flex items-center gap-2 bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-800">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          className="hidden"
          id="mars-surface-upload"
        />
        <label
          htmlFor="mars-surface-upload"
          className="text-xs font-medium text-orange-400 hover:text-orange-300 cursor-pointer"
        >
          {imageUrl ? 'Change Surface Image' : 'Upload Mars Image'}
        </label>

        {imageUrl && (
          <button
            type="button"
            onClick={handleResetTexture}
            className="text-xs text-slate-400 hover:text-white border-l border-slate-700 pl-2 cursor-pointer"
          >
            Reset
          </button>
        )}

        {fileName && (
          <span className="text-[11px] font-mono text-slate-400 max-w-[140px] truncate">
            {fileName}
          </span>
        )}
      </div>

      <Canvas camera={{ position: [0, 1.5, 5.6], fov: 45 }}>
        <ambientLight intensity={0.25} color="#ffd8b8" />
        <directionalLight position={[8, 5, 6]} intensity={1.45} color="#ffedd5" />
        <directionalLight position={[-6, -3, -5]} intensity={0.3} color="#94a3b8" />

        <MarsPlanetWithLights population={population} surfaceTextureUrl={activeTextureUrl} />

        <OrbitControls
          enableZoom={true}
          minDistance={3.2}
          maxDistance={10}
        />
      </Canvas>

      <div className="absolute bottom-3 left-4 text-xs font-mono text-slate-300 pointer-events-none bg-slate-900/90 px-3 py-1.5 rounded border border-slate-800">
        ORBITAL TELEMETRY: {activeBeaconCount} ACTIVE SETTLEMENT {activeBeaconCount === 1 ? 'BEACON' : 'BEACONS'} (POP: {population})
      </div>
    </div>
  );
}