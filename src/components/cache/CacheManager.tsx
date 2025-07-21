import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api';
import { 
  Card, 
  Button, 
  Progress, 
  Badge, 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger,
  Switch,
  Label,
  Input
} from '../ui';
import { 
  Database, 
  Trash2, 
  Settings, 
  BarChart3, 
  RefreshCw,
  Download,
  AlertCircle,
  CheckCircle,
  TrendingUp,
  HardDrive
} from 'lucide-react';
import { useToast } from '../ui/use-toast';

interface CacheStats {
  total_entries: number;
  total_size_bytes: number;
  hit_count: number;
  miss_count: number;
  eviction_count: number;
  expired_count: number;
  hit_ratio: number;
  memory_usage_mb: number;
}

interface CacheConfig {
  max_size_mb: number;
  max_entries: number;
  enable_http_cache: boolean;
  enable_file_cache: boolean;
  cleanup_interval: { secs: number; nanos: number };
}

interface CacheConfigUpdate {
  max_size_mb?: number;
  max_entries?: number;
  enable_http_cache?: boolean;
  enable_file_cache?: boolean;
  cleanup_interval_seconds?: number;
}

export function CacheManager() {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [config, setConfig] = useState<CacheConfig | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [configLoading, setConfigLoading] = useState(false);
  const { toast } = useToast();

  // Configuration form state
  const [maxSizeMb, setMaxSizeMb] = useState<number>(500);
  const [maxEntries, setMaxEntries] = useState<number>(10000);
  const [enableHttpCache, setEnableHttpCache] = useState<boolean>(true);
  const [enableFileCache, setEnableFileCache] = useState<boolean>(true);
  const [cleanupIntervalSeconds, setCleanupIntervalSeconds] = useState<number>(300);

  useEffect(() => {
    loadCacheData();
  }, []);

  const loadCacheData = async () => {
    try {
      setLoading(true);
      const [statsData, configData, recommendationsData] = await Promise.all([
        invoke<CacheStats>('get_cache_stats'),
        invoke<CacheConfig>('get_cache_config'),
        invoke<string[]>('get_cache_recommendations')
      ]);

      setStats(statsData);
      setConfig(configData);
      setRecommendations(recommendationsData);

      // Update form state with current config
      setMaxSizeMb(configData.max_size_mb);
      setMaxEntries(configData.max_entries);
      setEnableHttpCache(configData.enable_http_cache);
      setEnableFileCache(configData.enable_file_cache);
      setCleanupIntervalSeconds(configData.cleanup_interval.secs);
    } catch (error) {
      console.error('Failed to load cache data:', error);
      toast({
        title: "Error",
        description: "Failed to load cache data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    try {
      await invoke('clear_cache');
      await loadCacheData();
      toast({
        title: "Success",
        description: "Cache cleared successfully",
      });
    } catch (error) {
      console.error('Failed to clear cache:', error);
      toast({
        title: "Error",
        description: "Failed to clear cache",
        variant: "destructive",
      });
    }
  };

  const handleCleanupCache = async () => {
    try {
      const removedCount = await invoke<number>('cleanup_cache');
      await loadCacheData();
      toast({
        title: "Success",
        description: `Cleaned up ${removedCount} expired entries`,
      });
    } catch (error) {
      console.error('Failed to cleanup cache:', error);
      toast({
        title: "Error",
        description: "Failed to cleanup cache",
        variant: "destructive",
      });
    }
  };

  const handleUpdateConfig = async () => {
    try {
      setConfigLoading(true);
      const configUpdate: CacheConfigUpdate = {
        max_size_mb: maxSizeMb,
        max_entries: maxEntries,
        enable_http_cache: enableHttpCache,
        enable_file_cache: enableFileCache,
        cleanup_interval_seconds: cleanupIntervalSeconds,
      };

      await invoke('update_cache_config', { configUpdate });
      await loadCacheData();
      toast({
        title: "Success",
        description: "Cache configuration updated successfully",
      });
    } catch (error) {
      console.error('Failed to update cache config:', error);
      toast({
        title: "Error",
        description: "Failed to update cache configuration",
        variant: "destructive",
      });
    } finally {
      setConfigLoading(false);
    }
  };

  const handleExportMetrics = async () => {
    try {
      const metrics = await invoke<string>('export_cache_metrics');
      
      // Create and download file
      const blob = new Blob([metrics], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cache-metrics-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      toast({
        title: "Success",
        description: "Cache metrics exported successfully",
      });
    } catch (error) {
      console.error('Failed to export metrics:', error);
      toast({
        title: "Error",
        description: "Failed to export cache metrics",
        variant: "destructive",
      });
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const getPerformanceColor = (ratio: number) => {
    if (ratio >= 0.8) return 'text-green-600';
    if (ratio >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceBadge = (ratio: number) => {
    if (ratio >= 0.8) return { variant: 'default' as const, text: 'Excellent' };
    if (ratio >= 0.6) return { variant: 'secondary' as const, text: 'Good' };
    if (ratio >= 0.3) return { variant: 'outline' as const, text: 'Fair' };
    return { variant: 'destructive' as const, text: 'Poor' };
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center space-x-2">
          <RefreshCw className="h-4 w-4 animate-spin" />
          <span>Loading cache data...</span>
        </div>
      </div>
    );
  }

  if (!stats || !config) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center space-x-2 text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span>Failed to load cache data</span>
        </div>
      </div>
    );
  }

  const performanceBadge = getPerformanceBadge(stats.hit_ratio);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center space-x-2">
            <Database className="h-8 w-8" />
            <span>Cache Management</span>
          </h1>
          <p className="text-muted-foreground mt-1">
            Monitor and optimize caching performance for improved efficiency
          </p>
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={loadCacheData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExportMetrics}>
            <Download className="h-4 w-4 mr-2" />
            Export Metrics
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Performance Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Hit Ratio</p>
                  <p className={`text-3xl font-bold ${getPerformanceColor(stats.hit_ratio)}`}>
                    {(stats.hit_ratio * 100).toFixed(1)}%
                  </p>
                  <Badge variant={performanceBadge.variant} className="mt-2">
                    {performanceBadge.text}
                  </Badge>
                </div>
                <TrendingUp className="h-8 w-8 text-primary" />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Memory Usage</p>
                  <p className="text-3xl font-bold">
                    {stats.memory_usage_mb.toFixed(1)} MB
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">
                    of {config.max_size_mb} MB limit
                  </p>
                </div>
                <HardDrive className="h-8 w-8 text-blue-500" />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Entries</p>
                  <p className="text-3xl font-bold">{stats.total_entries.toLocaleString()}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    of {config.max_entries.toLocaleString()} limit
                  </p>
                </div>
                <Database className="h-8 w-8 text-purple-500" />
              </div>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Cache Size</p>
                  <p className="text-3xl font-bold">{formatBytes(stats.total_size_bytes)}</p>
                  <p className="text-sm text-green-600 mt-1">
                    {stats.hit_count + stats.miss_count} total requests
                  </p>
                </div>
                <BarChart3 className="h-8 w-8 text-green-500" />
              </div>
            </Card>
          </div>

          {/* Usage Progress */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Memory Usage</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Used: {stats.memory_usage_mb.toFixed(1)} MB</span>
                  <span>Limit: {config.max_size_mb} MB</span>
                </div>
                <Progress 
                  value={(stats.memory_usage_mb / config.max_size_mb) * 100} 
                  className="h-3"
                />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Entry Count</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span>Used: {stats.total_entries.toLocaleString()}</span>
                  <span>Limit: {config.max_entries.toLocaleString()}</span>
                </div>
                <Progress 
                  value={(stats.total_entries / config.max_entries) * 100} 
                  className="h-3"
                />
              </div>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
            <div className="flex space-x-4">
              <Button variant="outline" onClick={handleCleanupCache}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Cleanup Expired
              </Button>
              <Button variant="destructive" onClick={handleClearCache}>
                <Trash2 className="h-4 w-4 mr-2" />
                Clear All Cache
              </Button>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="statistics" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Detailed Statistics</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Cache Hits</p>
                <p className="text-2xl font-bold text-green-600">{stats.hit_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Cache Misses</p>
                <p className="text-2xl font-bold text-red-600">{stats.miss_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Evictions</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.eviction_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Expired</p>
                <p className="text-2xl font-bold text-gray-600">{stats.expired_count.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Hit Ratio</p>
                <p className={`text-2xl font-bold ${getPerformanceColor(stats.hit_ratio)}`}>
                  {(stats.hit_ratio * 100).toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Total Size</p>
                <p className="text-2xl font-bold">{formatBytes(stats.total_size_bytes)}</p>
              </div>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="configuration" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Cache Configuration</h3>
              <Button onClick={handleUpdateConfig} disabled={configLoading}>
                {configLoading ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Settings className="h-4 w-4 mr-2" />
                )}
                Update Config
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="maxSize">Maximum Size (MB)</Label>
                  <Input
                    id="maxSize"
                    type="number"
                    value={maxSizeMb}
                    onChange={(e) => setMaxSizeMb(Number(e.target.value))}
                    min="1"
                    max="10000"
                  />
                </div>
                <div>
                  <Label htmlFor="maxEntries">Maximum Entries</Label>
                  <Input
                    id="maxEntries"
                    type="number"
                    value={maxEntries}
                    onChange={(e) => setMaxEntries(Number(e.target.value))}
                    min="100"
                    max="1000000"
                  />
                </div>
                <div>
                  <Label htmlFor="cleanupInterval">Cleanup Interval (seconds)</Label>
                  <Input
                    id="cleanupInterval"
                    type="number"
                    value={cleanupIntervalSeconds}
                    onChange={(e) => setCleanupIntervalSeconds(Number(e.target.value))}
                    min="60"
                    max="3600"
                  />
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="httpCache"
                    checked={enableHttpCache}
                    onCheckedChange={setEnableHttpCache}
                  />
                  <Label htmlFor="httpCache">Enable HTTP Response Caching</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="fileCache"
                    checked={enableFileCache}
                    onCheckedChange={setEnableFileCache}
                  />
                  <Label htmlFor="fileCache">Enable File Content Caching</Label>
                </div>
              </div>
            </div>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Performance Recommendations</h3>
            <div className="space-y-3">
              {recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-muted rounded-lg">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm">{recommendation}</p>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
