import { Activity, AlertTriangle, Car, ShieldCheck } from 'lucide-react';

export default function Sidebar({ metrics }) {
  return (
    <aside className="w-64 bg-dark-800 border-r border-dark-700 flex flex-col">
      <div className="h-16 flex items-center px-6 border-b border-dark-700">
        <ShieldCheck className="text-brand-blue w-6 h-6 mr-2" />
        <span className="font-bold text-lg">ReliabilityOS</span>
      </div>
      
      <div className="p-6 flex-1">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Fleet Status</h3>
        
        <div className="space-y-4">
          <MetricCard 
            icon={<Car className="text-gray-400" />}
            label="Active Vehicles"
            value={metrics.vehicles}
          />
          <MetricCard 
            icon={<Activity className="text-brand-green" />}
            label="Health Score"
            value={`${metrics.health}%`}
          />
          <MetricCard 
            icon={<AlertTriangle className={metrics.alerts > 0 ? "text-brand-red" : "text-gray-400"} />}
            label="Critical Alerts"
            value={metrics.alerts}
          />
        </div>
      </div>
      
      <div className="p-4 border-t border-dark-700 text-xs text-gray-500 text-center">
        Powered by ReliabilityOS
      </div>
    </aside>
  );
}

function MetricCard({ icon, label, value }) {
  return (
    <div className="bg-dark-900 rounded-lg p-4 flex items-center shadow-inner">
      <div className="p-2 bg-dark-800 rounded-md mr-4">
        {icon}
      </div>
      <div>
        <div className="text-xs text-gray-400">{label}</div>
        <div className="text-xl font-bold">{value}</div>
      </div>
    </div>
  );
}
