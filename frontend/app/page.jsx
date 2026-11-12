'use client';

import { useState, useEffect } from "react";
import MarsCanvas from "@/components/MarsCanva";
import { Activity, Users, Utensils, ShieldAlert, Play, RefreshCw } from 'lucide-react';


export default function ColonyDashboard(){
  
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [tickMessage, setTickMessage] = useState(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

  const fetchStatus = async () => {
    try{
      const res = await fetch(`${API_URL}/api/colony/status`);
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch colony status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(()=>{
    fetchStatus();
  }, []);

  const handleSimulateTick = async () => {
    
    setSimulating(true);
    setTickMessage(null);

    try {
      const res = await fetch(`${API_URL}/api/colony/simulation-tick?days=1`, {
        method: 'POST',
      });

      const data = await res.json();
      setTickMessage(data.message);
      await fetchStatus(); // We use that to fresh telemetry stats 

    } catch (err) {
      console.error('Simulation tick failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="flex items-center space-x-3 text-orange-500 animate-pulse">
          <RefreshCw className="w-6 h-6 animate-spin" />
          <span className="text-xl font-mono">Establishing Telemetry Link with Mars...</span>
        </div>
      </div>
    );
  }

}