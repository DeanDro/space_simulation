'use client'
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