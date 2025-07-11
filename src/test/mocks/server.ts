import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'

// Define handlers for mocking API requests
export const handlers = [
  // Mock Tauri invoke calls
  http.post('/api/tauri', () => {
    return HttpResponse.json({ status: 'success' })
  }),

  // Mock external API calls
  http.get('/api/books/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      title: 'Mock Book',
      author: 'Mock Author',
      isbn: '123456789',
    })
  }),

  // Mock scraping endpoints
  http.post('/api/scrape', () => {
    return HttpResponse.json({
      status: 'completed',
      progress: 100,
      data: [],
    })
  }),

  // Mock file operations
  http.post('/api/files/read', () => {
    return HttpResponse.json({ content: 'mock file content' })
  }),

  http.post('/api/files/write', () => {
    return HttpResponse.json({ success: true })
  }),
]

// Create the server with the handlers
export const server = setupServer(...handlers)
