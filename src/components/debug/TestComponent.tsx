import { useParams } from 'react-router-dom';

export function TestComponent() {
  const { projectId } = useParams<{ projectId: string }>();
  
  console.log('TestComponent: Rendered with projectId:', projectId);
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Test Component</h1>
      <p>Project ID: {projectId}</p>
      <p>URL: {window.location.href}</p>
    </div>
  );
}
