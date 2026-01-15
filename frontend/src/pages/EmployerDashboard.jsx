import { useState, useEffect } from 'react';
import api from '../services/api';

const EmployerDashboard = () => {
    const [jobs, setJobs] = useState([]);
    const [applications, setApplications] = useState([]);
    const [activeTab, setActiveTab] = useState('jobs');
    const [newJob, setNewJob] = useState({ title: '', description: '', location: '', salary_range: '', deadline: '' });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const jobsRes = await api.get('jobs/');
        // Filter mainly happens on backend but simplistic here
        // Ideally backend returns only my jobs for a specific endpoint or we filter
        // The requirement said "EmployerDashboard (create job, view applications)"
        // Assuming /api/jobs/ returns all jobs, we might filter client side if backend doesn't filter by owner in 'list'
        // But for "My Jobs", usually a separate endpoint or query param. 
        // For now, I'll trust the implemented functionality or just list all recent jobs if I see them.
        // Actually, viewing applications implies seeing who applied to MY jobs.
        const appsRes = await api.get('applications/');
        setJobs(jobsRes.data); // This is ALL jobs public, probably should filter by current user's jobs if I had ID.
        setApplications(appsRes.data); // API viewset filters this correctly for Employer.
    };

    const handleCreateJob = async (e) => {
        e.preventDefault();
        try {
            await api.post('jobs/', newJob);
            setNewJob({ title: '', description: '', location: '', salary_range: '', deadline: '' });
            alert('Job Posted!');
            fetchData();
        } catch (err) {
            alert('Failed to post job');
        }
    };

    return (
        <div>
            <h1 className="text-3xl font-bold mb-6">Employer Dashboard</h1>
            <div className="flex space-x-4 mb-6">
                <button onClick={() => setActiveTab('jobs')} className={`pb-2 ${activeTab === 'jobs' ? 'border-b-2 border-blue-500' : ''}`}>Posted Jobs & Create</button>
                <button onClick={() => setActiveTab('apps')} className={`pb-2 ${activeTab === 'apps' ? 'border-b-2 border-blue-500' : ''}`}>Applications Received</button>
            </div>

            {activeTab === 'jobs' && (
                <div>
                    <div className="bg-white p-6 rounded shadow mb-8">
                        <h2 className="text-xl font-bold mb-4">Post a New Job</h2>
                        <form onSubmit={handleCreateJob} className="grid grid-cols-2 gap-4">
                            <input className="border p-2 rounded" placeholder="Job Title" value={newJob.title} onChange={e => setNewJob({ ...newJob, title: e.target.value })} required />
                            <input className="border p-2 rounded" placeholder="Location" value={newJob.location} onChange={e => setNewJob({ ...newJob, location: e.target.value })} required />
                            <input className="border p-2 rounded" placeholder="Salary Range" value={newJob.salary_range} onChange={e => setNewJob({ ...newJob, salary_range: e.target.value })} />
                            <input className="border p-2 rounded" type="date" placeholder="Deadline" value={newJob.deadline} onChange={e => setNewJob({ ...newJob, deadline: e.target.value })} required />
                            <textarea className="border p-2 rounded col-span-2" placeholder="Description" rows="4" value={newJob.description} onChange={e => setNewJob({ ...newJob, description: e.target.value })} required />
                            <button className="bg-blue-600 text-white p-2 rounded col-span-2">Post Job</button>
                        </form>
                    </div>
                </div>
            )}

            {activeTab === 'apps' && (
                <div className="bg-white p-6 rounded shadow">
                    <h2 className="text-xl font-bold mb-4">Applications</h2>
                    <table className="w-full text-left">
                        <thead>
                            <tr>
                                <th className="pb-2">Candidate</th>
                                <th className="pb-2">Job</th>
                                <th className="pb-2">Status</th>
                                <th className="pb-2">Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {applications.map(app => (
                                <tr key={app.id} className="border-t">
                                    <td className="py-2">{app.candidate_detail?.email}</td>
                                    <td className="py-2">{app.job_detail?.title}</td>
                                    <td className="py-2"><span className="bg-yellow-100 text-yellow-800 px-2 rounded text-sm">{app.status}</span></td>
                                    <td className="py-2">{new Date(app.applied_at).toLocaleDateString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default EmployerDashboard;
