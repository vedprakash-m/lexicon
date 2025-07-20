import { CheckCircle, Clock, Cpu } from 'lucide-react';
import { Badge } from '../ui';
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor';
import { useDashboardData } from '../../hooks/useDashboardData';

export function StatusBar() {
  const { data } = useDashboardData();
  const { metrics } = usePerformanceMonitor();
  
  const formatUptime = (uptimeSeconds: number) => {
    const hours = Math.floor(uptimeSeconds / 3600);
    const minutes = Math.floor((uptimeSeconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatMemoryUsage = (bytes: number) => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(0)} MB`;
  };

  const cpuUsage = metrics?.cpu_usage || data?.performance?.cpu_usage || 0;
  const uptimeSeconds = metrics ? 
    (metrics.uptime.secs + (metrics.uptime.nanos / 1_000_000_000)) : 
    (data?.performance ? (data.performance.uptime.secs + (data.performance.uptime.nanos / 1_000_000_000)) : 0);
  const memoryUsage = metrics?.memory_usage || data?.performance?.memory_usage || 0;
  const totalBooks = data?.stats?.total_books || 0;

  return (
    <footer className="h-6 border-t border-border bg-muted/20 flex items-center justify-between px-4 text-xs text-muted-foreground">
      {/* Left section - System status */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-1">
          <CheckCircle className="h-3 w-3 text-green-500" />
          <span>System Ready</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <Cpu className="h-3 w-3" />
          <span>CPU: {cpuUsage.toFixed(1)}%</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <Clock className="h-3 w-3" />
          <span>Uptime: {formatUptime(uptimeSeconds)}</span>
        </div>
      </div>

      {/* Center section - Current activity */}
      <div className="flex items-center space-x-2">
        <Badge variant="secondary" className="h-4 text-xs">
          Ready
        </Badge>
      </div>

      {/* Right section - Quick stats */}
      <div className="flex items-center space-x-4">
        <span>{totalBooks} books</span>
        <span>•</span>
        <span>{formatMemoryUsage(memoryUsage)}</span>
        <span>•</span>
        <span>v1.0.0</span>
      </div>
    </footer>
  );
}
