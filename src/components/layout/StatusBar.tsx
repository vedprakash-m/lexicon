import { CheckCircle, Clock, Cpu } from 'lucide-react';
import { Badge } from '../ui';

export function StatusBar() {
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
          <span>CPU: 12%</span>
        </div>
        
        <div className="flex items-center space-x-1">
          <Clock className="h-3 w-3" />
          <span>Uptime: 2h 14m</span>
        </div>
      </div>

      {/* Center section - Current activity */}
      <div className="flex items-center space-x-2">
        <Badge variant="secondary" className="h-4 text-xs">
          Processing: 2 files
        </Badge>
      </div>

      {/* Right section - Quick stats */}
      <div className="flex items-center space-x-4">
        <span>247 books</span>
        <span>•</span>
        <span>2.4 GB</span>
        <span>•</span>
        <span>v1.0.0</span>
      </div>
    </footer>
  );
}
