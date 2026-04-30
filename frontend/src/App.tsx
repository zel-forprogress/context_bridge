import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ConversationsPage from './pages/ConversationsPage'
import ConversationDetailPage from './pages/ConversationDetailPage'
import SummariesPage from './pages/SummariesPage'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/agents/:agentName/conversations" element={<ConversationsPage />} />
          <Route path="/conversations/:agentName/:sessionId" element={<ConversationDetailPage />} />
          <Route path="/summaries" element={<SummariesPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
