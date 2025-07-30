import { useState } from 'react';
import useStore from '../store/useStore';
import { SparklesIcon } from '@heroicons/react/24/outline';

function CreateAssignment() {
  const { createAssignment, loading, error, clearError } = useStore();
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState(null);

  const samplePrompts = [
    "The patient P001 is required Exercise today can you assign available employee.",
    "Patient P002 needs medication assistance at 10:00 AM.",
    "Assign a nurse to patient P003 for medicine administration urgently.",
    "Patient P004 requires companionship service this afternoon.",
    "Find a carer for patient P005 who needs personal care assistance."
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim()) {
      alert('Please enter a request');
      return;
    }

    try {
      clearError();
      setResult(null);
      const response = await createAssignment(prompt);
      setResult(response);
      setPrompt(''); // Clear prompt on success
    } catch (err) {
      console.error('Assignment failed:', err);
    }
  };

  const useSamplePrompt = (samplePrompt) => {
    setPrompt(samplePrompt);
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Create Assignment</h2>

      <div className="max-w-4xl mx-auto">
        {/* AI Assistant Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <SparklesIcon className="h-5 w-5 text-blue-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">AI-Powered Assignment</h3>
              <p className="mt-1 text-sm text-blue-700">
                Use natural language to request employee assignments. The AI will analyze requirements
                and find the best match based on qualifications, location, language, and availability.
              </p>
            </div>
          </div>
        </div>

        {/* Assignment Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="prompt" className="block text-sm font-medium text-gray-700">
              Assignment Request
            </label>
            <div className="mt-1">
              <textarea
                id="prompt"
                rows={4}
                className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Describe your assignment request in natural language..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading || !prompt.trim()}
              className={`px-6 py-3 rounded-md text-white font-medium ${
                loading || !prompt.trim()
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {loading ? 'Processing...' : 'Create Assignment'}
            </button>
          </div>
        </form>

        {/* Sample Prompts */}
        <div className="mt-8">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Sample Requests</h3>
          <div className="space-y-2">
            {samplePrompts.map((sample, index) => (
              <button
                key={index}
                onClick={() => useSamplePrompt(sample)}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
              >
                "{sample}"
              </button>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Success Result */}
        {result && result.success && result.assignment && (
          <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-green-900 mb-4">Assignment Created Successfully!</h3>
            
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium text-gray-700">Employee:</span>
                <span className="ml-2">{result.assignment.employee_name} ({result.assignment.employee_id})</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Patient:</span>
                <span className="ml-2">{result.assignment.patient_name} ({result.assignment.patient_id})</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Service Type:</span>
                <span className="ml-2 capitalize">{result.assignment.service_type}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Scheduled Time:</span>
                <span className="ml-2">{result.assignment.assigned_time}</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Duration:</span>
                <span className="ml-2">{result.assignment.estimated_duration} minutes</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Travel Time:</span>
                <span className="ml-2">{result.assignment.travel_time} minutes</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Priority Score:</span>
                <span className="ml-2">{result.assignment.priority_score}/10</span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Reason:</span>
                <p className="mt-1 text-gray-600">{result.assignment.assignment_reason}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CreateAssignment;
