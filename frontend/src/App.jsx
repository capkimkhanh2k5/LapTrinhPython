import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import JobList from './pages/JobList';
import EmployerDashboard from './pages/EmployerDashboard';
import CandidateDashboard from './pages/CandidateDashboard';
import Navbar from './components/Navbar';

const PrivateRoute = ({ children, role }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (role === 'employer' && !user.is_employer) return <Navigate to="/" />;
  if (role === 'candidate' && !user.is_candidate) return <Navigate to="/" />;
  return children;
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<JobList />} />
      <Route
        path="/dashboard/employer"
        element={
          <PrivateRoute role="employer">
            <EmployerDashboard />
          </PrivateRoute>
        }
      />
      <Route
        path="/dashboard/candidate"
        element={
          <PrivateRoute role="candidate">
            <CandidateDashboard />
          </PrivateRoute>
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Navbar />
          <div className="container mx-auto px-4 py-8">
            <AppRoutes />
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
