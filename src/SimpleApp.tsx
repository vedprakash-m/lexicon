import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import { 
  ThemeProvider, 
  ToastProvider, 
  TooltipProvider 
} from './components/ui';
import './App.css';

function SimpleApp() {
  console.log('SimpleApp.tsx: Rendering simplified Lexicon interface');
  
  return (
    <ThemeProvider defaultTheme="system" storageKey="lexicon-theme">
      <TooltipProvider>
        <ToastProvider>
          <Router>
            <div className="min-h-screen bg-background">
              <header className="border-b">
                <div className="container mx-auto px-4 py-4">
                  <h1 className="text-2xl font-bold">🎉 Lexicon - Universal RAG Dataset Preparation</h1>
                </div>
              </header>
              
              <div className="container mx-auto px-4 py-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-card text-card-foreground rounded-lg border p-6">
                    <h2 className="text-xl font-semibold mb-4">Dashboard</h2>
                    <p className="text-muted-foreground">Welcome to Lexicon! The full interface is loading.</p>
                  </div>
                  
                  <div className="bg-card text-card-foreground rounded-lg border p-6">
                    <h2 className="text-xl font-semibold mb-4">Features</h2>
                    <ul className="space-y-2 text-sm">
                      <li>✅ Universal text processing</li>
                      <li>✅ Advanced chunking strategies</li>
                      <li>✅ Quality analysis</li>
                      <li>✅ Export management</li>
                    </ul>
                  </div>
                  
                  <div className="bg-card text-card-foreground rounded-lg border p-6">
                    <h2 className="text-xl font-semibold mb-4">System Status</h2>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        React Router working
                      </div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        Tailwind CSS loaded
                      </div>
                      <div className="flex items-center">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                        Theme provider active
                      </div>
                    </div>
                  </div>
                </div>
                
                <Routes>
                  <Route path="/" element={
                    <div className="mt-8 text-center">
                      <p className="text-lg">This is a simplified view. Opening developer tools (Cmd+Shift+I) to check for errors...</p>
                    </div>
                  } />
                </Routes>
              </div>
            </div>
          </Router>
        </ToastProvider>
      </TooltipProvider>
    </ThemeProvider>
  );
}

export default SimpleApp;
