import React, { useState } from 'react';
import { Settings as SettingsIcon, User, Bell, Cloud, Palette, Monitor, ShieldCheck } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, Button, Tabs, TabsList, TabsTrigger, TabsContent } from '../ui';
import { ThemeToggle } from '../ui/theme-toggle';
import { useLexiconStore } from '../../store';

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const { settings, updateSettings } = useLexiconStore();
  const [activeTab, setActiveTab] = useState('general');

  const handleSave = () => {
    // Settings are automatically saved via the store
    // You could add a toast notification here
    onClose();
  };

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <SettingsIcon className="h-5 w-5" />
            Settings
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex">
            <div className="w-48 border-r">
              <TabsList className="flex flex-col h-auto w-full bg-transparent p-1">
                <TabsTrigger value="general" className="w-full justify-start">
                  <User className="h-4 w-4 mr-2" />
                  General
                </TabsTrigger>
                <TabsTrigger value="appearance" className="w-full justify-start">
                  <Palette className="h-4 w-4 mr-2" />
                  Appearance
                </TabsTrigger>
                <TabsTrigger value="notifications" className="w-full justify-start">
                  <Bell className="h-4 w-4 mr-2" />
                  Notifications
                </TabsTrigger>
                <TabsTrigger value="sync" className="w-full justify-start">
                  <Cloud className="h-4 w-4 mr-2" />
                  Cloud Sync
                </TabsTrigger>
                <TabsTrigger value="privacy" className="w-full justify-start">
                  <ShieldCheck className="h-4 w-4 mr-2" />
                  Privacy
                </TabsTrigger>
                <TabsTrigger value="advanced" className="w-full justify-start">
                  <Monitor className="h-4 w-4 mr-2" />
                  Advanced
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="flex-1 overflow-y-auto">
              <TabsContent value="general" className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">General Settings</h3>
                  
                  {/* Language */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium">Language</label>
                    <select
                      value={settings.language}
                      onChange={(e) => updateSettings({ language: e.target.value as any })}
                      className="w-full rounded border border-input bg-background px-3 py-2"
                    >
                      <option value="en">English</option>
                      <option value="es">Español</option>
                      <option value="fr">Français</option>
                      <option value="de">Deutsch</option>
                    </select>
                  </div>

                  {/* Auto Save */}
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium">Auto-save changes</div>
                      <div className="text-xs text-muted-foreground">
                        Automatically save your work as you make changes
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      checked={settings.autoSave}
                      onChange={(e) => updateSettings({ autoSave: e.target.checked })}
                      className="rounded border-input"
                    />
                  </div>

                  {/* Backup Frequency */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium">Backup Frequency</label>
                    <select
                      value={settings.backupFrequency}
                      onChange={(e) => updateSettings({ backupFrequency: e.target.value as any })}
                      className="w-full rounded border border-input bg-background px-3 py-2"
                    >
                      <option value="none">Never</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </select>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="appearance" className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Appearance</h3>
                  
                  {/* Theme */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium">Theme</label>
                    <div className="flex items-center gap-4">
                      <ThemeToggle />
                      <span className="text-sm text-muted-foreground">
                        Choose between light, dark, or system theme
                      </span>
                    </div>
                  </div>

                  {/* Density */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium">Interface Density</label>
                    <select className="w-full rounded border border-input bg-background px-3 py-2">
                      <option value="comfortable">Comfortable</option>
                      <option value="compact">Compact</option>
                      <option value="spacious">Spacious</option>
                    </select>
                  </div>

                  {/* Animations */}
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium">Enable animations</div>
                      <div className="text-xs text-muted-foreground">
                        Show smooth transitions and animations
                      </div>
                    </div>
                    <input
                      type="checkbox"
                      defaultChecked={true}
                      className="rounded border-input"
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="notifications" className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Notification Settings</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Processing complete notifications</div>
                        <div className="text-xs text-muted-foreground">
                          Notify when document processing finishes
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.notifications.processingComplete}
                        onChange={(e) => updateSettings({
                          notifications: {
                            ...settings.notifications,
                            processingComplete: e.target.checked
                          }
                        })}
                        className="rounded border-input"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Error notifications</div>
                        <div className="text-xs text-muted-foreground">
                          Notify when errors occur
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.notifications.errors}
                        onChange={(e) => updateSettings({
                          notifications: {
                            ...settings.notifications,
                            errors: e.target.checked
                          }
                        })}
                        className="rounded border-input"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Update notifications</div>
                        <div className="text-xs text-muted-foreground">
                          Notify about app updates
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.notifications.updates}
                        onChange={(e) => updateSettings({
                          notifications: {
                            ...settings.notifications,
                            updates: e.target.checked
                          }
                        })}
                        className="rounded border-input"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Cloud sync notifications</div>
                        <div className="text-xs text-muted-foreground">
                          Notify about sync status and conflicts
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.notifications.cloudSync}
                        onChange={(e) => updateSettings({
                          notifications: {
                            ...settings.notifications,
                            cloudSync: e.target.checked
                          }
                        })}
                        className="rounded border-input"
                      />
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="sync" className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Cloud Sync Settings</h3>
                  
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-sm font-medium">Sync Provider</label>
                      <select 
                        value={settings.cloudSync.provider}
                        onChange={(e) => updateSettings({
                          cloudSync: {
                            ...settings.cloudSync,
                            provider: e.target.value as any
                          }
                        })}
                        className="w-full rounded border border-input bg-background px-3 py-2"
                      >
                        <option value="none">None</option>
                        <option value="icloud">iCloud</option>
                        <option value="google_drive">Google Drive</option>
                        <option value="dropbox">Dropbox</option>
                      </select>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Auto-sync</div>
                        <div className="text-xs text-muted-foreground">
                          Automatically sync changes to the cloud
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        checked={settings.cloudSync.autoSync}
                        onChange={(e) => updateSettings({
                          cloudSync: {
                            ...settings.cloudSync,
                            autoSync: e.target.checked
                          }
                        })}
                        className="rounded border-input"
                      />
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="privacy" className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Privacy & Security</h3>
                  
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Analytics & telemetry</div>
                        <div className="text-xs text-muted-foreground">
                          Help improve Lexicon by sharing anonymous usage data
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        defaultChecked={false}
                        className="rounded border-input"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Crash reports</div>
                        <div className="text-xs text-muted-foreground">
                          Automatically send crash reports to help fix bugs
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        defaultChecked={true}
                        className="rounded border-input"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium">Data retention</label>
                      <select className="w-full rounded border border-input bg-background px-3 py-2">
                        <option value="1month">1 month</option>
                        <option value="3months">3 months</option>
                        <option value="6months">6 months</option>
                        <option value="1year">1 year</option>
                        <option value="forever">Keep forever</option>
                      </select>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="advanced" className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-medium mb-4">Advanced Settings</h3>
                  
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-sm font-medium">Performance Mode</label>
                      <select className="w-full rounded border border-input bg-background px-3 py-2">
                        <option value="balanced">Balanced</option>
                        <option value="performance">High Performance</option>
                        <option value="battery">Battery Saver</option>
                      </select>
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium">Memory limit (MB)</label>
                      <input
                        type="number"
                        defaultValue={2048}
                        min={512}
                        max={8192}
                        className="w-full rounded border border-input bg-background px-3 py-2"
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium">Developer mode</div>
                        <div className="text-xs text-muted-foreground">
                          Enable advanced debugging features
                        </div>
                      </div>
                      <input
                        type="checkbox"
                        defaultChecked={false}
                        className="rounded border-input"
                      />
                    </div>

                    <div className="pt-4 border-t">
                      <Button variant="outline" className="w-full">
                        Reset to Defaults
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>

        <div className="border-t pt-4 flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Changes
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
