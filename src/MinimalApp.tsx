import React from 'react';

function MinimalApp() {
  const [count, setCount] = React.useState(0);
  
  React.useEffect(() => {
    console.log('MinimalApp mounted successfully');
    document.title = 'Lexicon - Test App Working';
  }, []);

  return (
    <div style={{
      padding: '40px',
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f9ff',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <h1 style={{
        color: '#0f172a',
        fontSize: '3rem',
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        🎉 Lexicon is Working!
      </h1>
      
      <div style={{
        backgroundColor: 'white',
        padding: '30px',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        maxWidth: '600px',
        textAlign: 'center'
      }}>
        <p style={{ fontSize: '1.2rem', marginBottom: '20px', color: '#334155' }}>
          If you can see this, the React app is loading correctly!
        </p>
        
        <p style={{ fontSize: '1rem', marginBottom: '20px', color: '#64748b' }}>
          Click count: <strong style={{color: '#0ea5e9'}}>{count}</strong>
        </p>
        
        <button 
          onClick={() => setCount(c => c + 1)}
          style={{
            backgroundColor: '#0ea5e9',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            fontSize: '1rem',
            borderRadius: '8px',
            cursor: 'pointer',
            marginRight: '10px'
          }}
        >
          Increment Counter
        </button>
        
        <button 
          onClick={() => {
            console.log('JavaScript is working perfectly! Test button clicked.');
          }}
          style={{
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            fontSize: '1rem',
            borderRadius: '8px',
            cursor: 'pointer'
          }}
        >
          Test Console Log
        </button>
      </div>
      
      <div style={{
        marginTop: '30px',
        padding: '20px',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderRadius: '8px',
        border: '1px solid #10b981'
      }}>
        <h3 style={{color: '#065f46', marginBottom: '10px'}}>✅ System Status:</h3>
        <ul style={{listStyle: 'none', padding: 0, margin: 0}}>
          <li style={{color: '#065f46', marginBottom: '5px'}}>• React is rendering</li>
          <li style={{color: '#065f46', marginBottom: '5px'}}>• JavaScript is executing</li>
          <li style={{color: '#065f46', marginBottom: '5px'}}>• State management is working</li>
          <li style={{color: '#065f46', marginBottom: '5px'}}>• CSS styles are applied</li>
        </ul>
      </div>
      
      <p style={{
        marginTop: '20px',
        fontSize: '0.9rem',
        color: '#64748b',
        textAlign: 'center'
      }}>
        Try pressing <strong>Cmd+Shift+I</strong> or <strong>F12</strong> to open developer tools
      </p>
    </div>
  );
}

export default MinimalApp;
