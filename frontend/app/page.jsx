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

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-800 pb-6 gap-4">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-orange-500 flex items-center gap-2">
              <Activity className="w-8 h-8" /> ARES-1 COLONY COMMAND
            </h1>
            <p className="text-slate-400 text-sm mt-1">Real-Time Telemetry & Simulation Progression Engine</p>
          </div>
          <button
            onClick={handleSimulateTick}
            disabled={simulating}
            className="bg-orange-600 hover:bg-orange-500 disabled:bg-slate-800 text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 transition-all shadow-lg shadow-orange-950/50 cursor-pointer"
          >
            <Play className={`w-4 h-4 ${simulating ? 'animate-spin' : ''}`} />
            {simulating ? 'Advancing Sol...' : 'Advance +1 Sol'}
          </button>
        </header>
        {tickMessage && (
          <div className="bg-orange-950/40 border border-orange-500/30 text-orange-200 px-4 py-3 rounded-lg text-sm font-mono flex items-center justify-between">
            <span>📢 {tickMessage}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Active Crew</p>
              <p className="text-3xl font-bold text-white mt-1">{status?.active_crew_members ?? 0}</p>
            </div>
            <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
              <Users className="w-6 h-6" />
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Total Food Stock</p>
              <p className="text-3xl font-bold text-white mt-1">
                {status?.total_food_stock_lbs ? Math.round(status.total_food_stock_lbs).toLocaleString() : 0} <span className="text-sm font-normal text-slate-400">lbs</span>
              </p>
            </div>
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Utensils className="w-6 h-6" />
            </div>
          </div>
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-lg flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm font-medium">Colony Status</p>
              <p className="text-2xl font-bold text-emerald-400 mt-1 flex items-center gap-2">
                <span className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></span>
                {status?.colony_status ?? 'Nominal'}
              </p>
            </div>
            <div className="p-3 bg-orange-500/10 text-orange-400 rounded-lg">
              <ShieldAlert className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Three.js 3D View */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-semibold text-slate-200">Orbital Planetary View</h2>
            <MarsCanvas />
          </div>

          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-slate-200">Habitat Statuses</h2>
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
              {status?.habitats?.map((hab) => (
                <div key={hab.pk} className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-semibold text-slate-100">{hab.location}</span>
                    <span className="text-xs bg-slate-800 text-slate-300 px-2 py-1 rounded">Family {hab.fkfamily}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-slate-400 pt-1 border-t border-slate-800/60">
                    <div>Integrity: <span className="text-white font-mono">{hab.structuralintegrity}%</span></div>
                    <div>Oxygen: <span className={hab.oxygensupply ? 'text-emerald-400 font-semibold' : 'text-red-400 font-semibold'}>{hab.oxygensupply ? 'OK' : 'FAIL'}</span></div>
                    <div>Water: <span className={hab.watersupply ? 'text-emerald-400 font-semibold' : 'text-red-400 font-semibold'}>{hab.watersupply ? 'OK' : 'FAIL'}</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  )

}