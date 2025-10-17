import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Overview from './pages/Overview';
import History from './pages/History';
import RequestDetail from './pages/RequestDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<Overview />} />
          <Route path="history" element={<History />} />
          <Route path="requests/:id" element={<RequestDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;