import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import { Home } from './components/Home'
import { SubmissionForm } from './components/Form';
import { Ranking } from './components/Ranking';
import { Submission } from './components/Submission';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/submit" element={<SubmissionForm />} />
        <Route path="/ranking" element={<Ranking />} />
        <Route path="/submission/:uuid" element={<Submission />} />
      </Routes>
    </Router>
  );
}

export default App;
