"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Mission {
  id: number;
  title: string;
  description?: string;
  required_skills?: string[];
  required_location?: string;
  required_seniority?: string;
}

interface MatchResult {
  profile_id: number;
  profile_name: string;
  score: number;
  skills_match: number;
  seniority_match: number;
  location_match: number;
}

export default function MatchingPage() {
  const [missions, setMissions] = useState<Mission[]>([]);
  const [selectedMission, setSelectedMission] = useState<Mission | null>(null);
  const [results, setResults] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch missions on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/missions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setMissions)
      .catch(() => setError("Failed to load missions"));
  }, []);

  const runMatching = async () => {
    if (!selectedMission) return;

    setLoading(true);
    setError(null);
    setResults([]);

    const token = localStorage.getItem("token");
    if (!token) {
      setError("Please login first");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/missions/${selectedMission.id}/match`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!res.ok) throw new Error("Matching failed");

      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Matching failed");
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-green-600 bg-green-100";
    if (score >= 0.6) return "text-blue-600 bg-blue-100";
    if (score >= 0.4) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getScoreBar = (score: number) => {
    const percentage = Math.round(score * 100);
    const color = score >= 0.8 ? "bg-green-500" : score >= 0.6 ? "bg-blue-500" : score >= 0.4 ? "bg-yellow-500" : "bg-red-500";
    return (
      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
        <div className={`${color} h-2 rounded-full transition-all duration-300`} style={{ width: `${percentage}%` }} />
      </div>
    );
  };

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">🎯 Matching</h1>
        <p className="mt-2 text-gray-600">Trouvez les meilleurs candidats pour vos missions</p>
      </div>

      {/* Mission Selection */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">1. Sélectionner une mission</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Mission</label>
            <select
              value={selectedMission?.id || ""}
              onChange={(e) => {
                const mission = missions.find((m) => m.id === Number(e.target.value));
                setSelectedMission(mission || null);
                setResults([]);
              }}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            >
              <option value="">-- Choisir une mission --</option>
              {missions.map((mission) => (
                <option key={mission.id} value={mission.id}>
                  {mission.title}
                </option>
              ))}
            </select>
          </div>

          {selectedMission && (
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Détails</label>
              <div className="flex flex-wrap gap-2">
                {selectedMission.required_skills?.map((skill) => (
                  <span key={skill} className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                    {skill}
                  </span>
                ))}
              </div>
              {selectedMission.required_location && (
                <p className="text-sm text-gray-600">📍 {selectedMission.required_location}</p>
              )}
              {selectedMission.required_seniority && (
                <p className="text-sm text-gray-600">👤 {selectedMission.required_seniority}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Run Matching Button */}
      <div className="flex justify-center mb-8">
        <button
          onClick={runMatching}
          disabled={!selectedMission || loading}
          className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-3 text-white font-semibold shadow-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Matching en cours...
            </>
          ) : (
            <>
              🚀 Lancer le matching
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-lg font-semibold text-gray-900">📊 Résultats ({results.length} candidats)</h2>
          </div>

          <div className="divide-y divide-gray-200">
            {results.map((result, index) => (
              <div key={result.profile_id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium text-gray-600">
                        #{index + 1}
                      </span>
                      <h3 className="text-lg font-semibold text-gray-900">{result.profile_name}</h3>
                      <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${getScoreColor(result.score)}`}>
                        {Math.round(result.score * 100)}%
                      </span>
                    </div>

                    <div className="mt-4 grid grid-cols-3 gap-4">
                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Skills</p>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900">{Math.round(result.skills_match * 100)}%</span>
                          <div className="flex-1">{getScoreBar(result.skills_match)}</div>
                        </div>
                      </div>

                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Seniority</p>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900">{Math.round(result.seniority_match * 100)}%</span>
                          <div className="flex-1">{getScoreBar(result.seniority_match)}</div>
                        </div>
                      </div>

                      <div>
                        <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Location</p>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-gray-900">{Math.round(result.location_match * 100)}%</span>
                          <div className="flex-1">{getScoreBar(result.location_match)}</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <button className="flex-shrink-0 inline-flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 transition-colors">
                    ✓ Shortlist
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!selectedMission && (
        <div className="text-center py-12">
          <div className="text-5xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900">Sélectionnez une mission</h3>
          <p className="mt-2 text-gray-500">Choisissez une mission pour lancer le matching</p>
        </div>
      )}

      {selectedMission && results.length === 0 && !loading && !error && (
        <div className="text-center py-12">
          <div className="text-5xl mb-4">🎯</div>
          <h3 className="text-lg font-medium text-gray-900">Prêt à matcher</h3>
          <p className="mt-2 text-gray-500">Cliquez sur "Lancer le matching" pour trouver les meilleurs candidats</p>
        </div>
      )}
    </main>
  );
}