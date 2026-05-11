import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6'];

export default function ChartPanel({ data }) {
  const { chartData, vehicleIds } = useMemo(() => {
    // Filter for LiDAR and reverse to chronologically order
    const filtered = data.filter(d => d.sensor_id === 'LiDAR').slice(0, 400).reverse();
    const timeMap = {};
    const vIds = new Set();
    
    filtered.forEach(d => {
      const t = new Date(d.timestamp).toLocaleTimeString();
      if (!timeMap[t]) timeMap[t] = { time: t };
      timeMap[t][d.vehicle_id] = d.temperature_c;
      vIds.add(d.vehicle_id);
    });
    
    // Convert to array
    const sortedData = Object.values(timeMap);
    // Take top 5 vehicles to keep chart readable
    const sortedIds = Array.from(vIds).sort().slice(0, 5);
    
    return { chartData: sortedData.slice(-30), vehicleIds: sortedIds };
  }, [data]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-dark-800 p-3 border border-dark-700 rounded shadow-lg">
          <p className="text-gray-400 text-xs mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }} className="font-bold text-sm">
              {entry.name}: {entry.value?.toFixed(1)}°C
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return <div className="flex h-full items-center justify-center text-gray-500">Waiting for telemetry...</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2d323c" vertical={false} />
        <XAxis 
          dataKey="time" 
          stroke="#6b7280" 
          fontSize={10} 
          tickFormatter={(val, i) => i % 5 === 0 ? val : ''} 
        />
        <YAxis 
          stroke="#6b7280" 
          fontSize={10} 
          domain={['auto', 'auto']}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: '12px' }} />
        {vehicleIds.map((id, index) => (
          <Line 
            key={id}
            type="monotone" 
            dataKey={id} 
            name={id}
            stroke={COLORS[index % COLORS.length]} 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
