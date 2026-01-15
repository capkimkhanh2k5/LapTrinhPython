import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="bg-white shadow">
            <div className="container mx-auto px-4">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <Link to="/" className="text-xl font-bold text-blue-600">Jobio</Link>
                        <div className="ml-10 flex items-baseline space-x-4">
                            <Link to="/" className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md text-sm font-medium">Jobs</Link>
                        </div>
                    </div>
                    <div className="flex items-center">
                        {user ? (
                            <div className="flex items-center space-x-4">
                                <span className="text-gray-700">Hello, {user.email}</span>
                                {user.is_employer && (
                                    <Link to="/dashboard/employer" className="text-gray-700 hover:text-blue-600">Dashboard</Link>
                                )}
                                {user.is_candidate && (
                                    <Link to="/dashboard/candidate" className="text-gray-700 hover:text-blue-600">Dashboard</Link>
                                )}
                                <button
                                    onClick={handleLogout}
                                    className="text-red-600 hover:text-red-800"
                                >
                                    Logout
                                </button>
                            </div>
                        ) : (
                            <div className="space-x-4">
                                <Link to="/login" className="text-blue-600 hover:text-blue-800">Login</Link>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
