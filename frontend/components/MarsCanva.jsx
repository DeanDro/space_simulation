'use client';
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Sphere } from "@react-three/drei";
import { useRef } from "react";


function MarsGlobe(){
    
    const meshRef = useRef();

    // add planet rotation
    useFrame((_, delta)=>{
        meshRef.current.rotation.y += delta *0.1;
    });

    return (
        <Sphere ref={meshRef} args={[2, 32, 32]}>
            <meshStandardMaterial
                color="#c1440e"
                roughness={0.8}
                metalness={0.2}
            />
        </Sphere>
    );
}

export default function MarsCanvas(){
    return (
        <div className="w-full h-[400px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative">
            <Canvas camera={{ position: [0, 0, 6] }}>
                <ambientLight intensity={0.6} />
                <directionalLight position={[5, 5, 5]} intensity={1.5} />
                <MarsGlobe />
                <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.4} />
            </Canvas>
            <div className="absolute bottom-3 left-4 text-xs font-mono text-slate-400 pointer-events-none bg-slate-900/80 px-2.5 py-1 rounded border border-slate-800">
                VISUALIZATION: MARS SURFACE / ORBITAL CAM
            </div>
        </div>
    );
}