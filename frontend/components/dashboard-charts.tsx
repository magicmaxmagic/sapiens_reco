"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const COLORS = ["#facc15", "#38bdf8", "#4ade80", "#f472b6", "#a78bfa", "#fb923c"];

interface ChartData {
  name: string;
  value: number;
}

interface TimeSeriesData {
  date: string;
  count: number;
}

interface ChartsProps {
  profileBySeniority: ChartData[];
  missionsByStatus: ChartData[];
  matchScoreDistribution: ChartData[];
  profileTrends: TimeSeriesData[];
  missionTrends: TimeSeriesData[];
}

export function DashboardCharts({
  profileBySeniority,
  missionsByStatus,
  matchScoreDistribution,
  profileTrends,
  missionTrends,
}: ChartsProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Profile by Seniority (Pie Chart) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Profils par séniorité</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={profileBySeniority}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  fill="#facc15"
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {profileBySeniority.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Missions by Status (Bar Chart) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Missions par statut</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={missionsByStatus}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="name" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip />
                <Bar dataKey="value" fill="#38bdf8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Match Score Distribution (Bar Chart) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Distribution des scores de matching</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={matchScoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="name" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip />
                <Bar dataKey="value" fill="#4ade80" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Trends (Line Chart) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Évolution temporelle</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  data={profileTrends}
                  dataKey="count"
                  stroke="#facc15"
                  name="Profils"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  data={missionTrends}
                  dataKey="count"
                  stroke="#38bdf8"
                  name="Missions"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}