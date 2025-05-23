import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ClientPage from './pages/ClientPage';
import SummaryPage from './pages/SummaryPage';
import DocumentsPage from './pages/DocumentsPage';
import Navbar from './components/Navbar';

function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Navbar />
        <main className="container mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/client/:id" element={<ClientPage />} />
            <Route path="/client/:id/summary" element={<SummaryPage />} />
            <Route path="/client/:id/documents" element={<DocumentsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
