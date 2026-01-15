import { useState, useEffect } from 'react';
import api from '../services/api';
import { Link } from 'react-router-dom';

const JobList = () => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchJobs = async () => {
            try {
                const res = await api.get('jobs/');
                setJobs(res.data);
            } catch (err) {
                console.error(err);
                setError('Failed to load jobs');
            } finally {
                setLoading(false);
            }
        };
        fetchJobs();
    }, []);

    const filteredJobs = jobs.filter(job =>
        job.title.toLowerCase().includes(search.toLowerCase()) ||
        job.location.toLowerCase().includes(search.toLowerCase())
    );

    const handleApply = async (jobId) => {
        try {
            await api.post('applications/', { job: jobId });
            alert('Applied successfully!');
        } catch (err) {
            alert('Failed to apply (Maybe you are not a candidate or already applied?)');
        }
    };

    if (loading) return <div className="text-center mt-10">Loading...</div>;

    return (
        <div>
            <div className="mb-8">
                <input
                    type="text"
                    placeholder="Search jobs by title or location..."
                    className="w-full p-4 border rounded shadow-sm"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {error && <p className="text-red-500">{error}</p>}

            <div className="grid gap-6">
                {filteredJobs.map(job => (
                    <div key={job.id} className="bg-white p-6 rounded-lg shadow hover:shadow-md transition">
                        <h3 className="text-xl font-bold mb-2">{job.title}</h3>
                        <p className="text-gray-600 mb-2">{job.employer?.employer_profile?.company_name} - {job.location}</p>
                        <p className="text-gray-800 mb-4">{job.salary_range} | Deadline: {job.deadline}</p>
                        <div className="flex justify-between items-center">
                            <span className="bg-blue-100 text-blue-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded">
                                {job.category || 'General'}
                            </span>
                            <button
                                onClick={() => handleApply(job.id)}
                                className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded"
                            >
                                Apply Now
                            </button>
                        </div>
                    </div>
                ))}
                {filteredJobs.length === 0 && <p className="text-center text-gray-500">No jobs found.</p>}
            </div>
        </div>
    );
};

export default JobList;
