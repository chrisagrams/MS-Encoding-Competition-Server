import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import { SubmissionForm } from './components/Form';
import { Ranking } from './components/Ranking';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/submit" element={<SubmissionForm />} />
        <Route path="/ranking" element={<Ranking />} />
      </Routes>
    </Router>
  );
}

export default App;
