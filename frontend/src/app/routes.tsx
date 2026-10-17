import { Navigate, type RouteObject } from 'react-router'
import { ChatPage } from '@/routes/ChatPage'
import { RootRedirect } from '@/routes/RootRedirect'

export const routes: RouteObject[] = [
  { path: '/', element: <RootRedirect /> },
  { path: '/:domain', element: <ChatPage /> },
  { path: '/:domain/c/:threadId', element: <ChatPage /> },
  { path: '*', element: <Navigate to="/" replace /> },
]
