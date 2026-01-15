import { useState, useEffect } from 'react';
import api from '../services/api';

const CandidateDashboard = () => {
    const [applications, setApplications] = useState([]);

    useEffect(() => {
        const fetchApps = async () => {
            const res = await api.get('applications/');
            setApplications(res.data);
        };
        fetchApps();
    }, []);

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">Candidate Dashboard</h1>
            <div className="bg-white p-6 rounded shadow">
                <h2 className="text-xl font-bold mb-4">My Applications</h2>
                {applications.length === 0 ? (
                    <p>You haven't applied to any jobs yet.</p>
                ) : (
                    <div className="space-y-4">
                        {applications.map(app => (
                            <div key={app.id} className="border p-4 rounded flex justify-between items-center">
                                <div>
                                    <h3 className="font-bold text-lg">{app.job_detail?.title}</h3>
                                    <p className="text-gray-600">{app.job_detail?.employer?.employer_profile?.company_name}</p>
                                    <p className="text-xs text-gray-400">Applied on: {new Date(app.applied_at).toLocaleDateString()}</p>
                                </div>
                                <div>
                                    <span className={`px-3 py-1 rounded-full text-sm font-semibold 
                                        ${app.status === 'accepted' ? 'bg-green-100 text-green-800' :
                                            app.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                        {app.status.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CandidateDashboard;
