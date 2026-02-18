'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createSubmission, generateSubmission, type SubmissionCreate } from '@/lib/api';

export default function SubmitPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<SubmissionCreate>({
    submission_type: '510k',
    device_name: '',
    device_description: '',
    manufacturer: '',
    indications_for_use: '',
    predicate_device_name: '',
    predicate_k_number: '',
  });
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setGenerating(true);
      setError(null);

      // Create submission
      const submission = await createSubmission(formData);

      // Generate documents
      await generateSubmission(submission.id, true, true);

      // Redirect to submission details
      router.push(`/submissions/${submission.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to create submission');
      setGenerating(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">New FDA Submission</h1>
        <p className="mt-2 text-gray-600">
          Create a new 510(k) premarket notification with AI-powered document generation
        </p>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-lg shadow p-6">
        {/* Submission Type */}
        <div>
          <label htmlFor="submission_type" className="block text-sm font-medium text-gray-700">
            Submission Type
          </label>
          <select
            id="submission_type"
            name="submission_type"
            value={formData.submission_type}
            onChange={handleChange}
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="510k">510(k) Premarket Notification</option>
            <option value="pma">PMA (Premarket Approval)</option>
            <option value="de_novo">De Novo Classification</option>
            <option value="ide">IDE (Investigational Device Exemption)</option>
          </select>
        </div>

        {/* Device Name */}
        <div>
          <label htmlFor="device_name" className="block text-sm font-medium text-gray-700">
            Device Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="device_name"
            name="device_name"
            value={formData.device_name}
            onChange={handleChange}
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="e.g., CardioMonitor Pro"
          />
        </div>

        {/* Manufacturer */}
        <div>
          <label htmlFor="manufacturer" className="block text-sm font-medium text-gray-700">
            Manufacturer
          </label>
          <input
            type="text"
            id="manufacturer"
            name="manufacturer"
            value={formData.manufacturer}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="e.g., MedTech Innovations Inc."
          />
        </div>

        {/* Device Description */}
        <div>
          <label htmlFor="device_description" className="block text-sm font-medium text-gray-700">
            Device Description
          </label>
          <textarea
            id="device_description"
            name="device_description"
            value={formData.device_description}
            onChange={handleChange}
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="Provide a detailed description of the device, its components, and how it works..."
          />
        </div>

        {/* Indications for Use */}
        <div>
          <label htmlFor="indications_for_use" className="block text-sm font-medium text-gray-700">
            Indications for Use
          </label>
          <textarea
            id="indications_for_use"
            name="indications_for_use"
            value={formData.indications_for_use}
            onChange={handleChange}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="Describe the intended use and patient population..."
          />
        </div>

        {/* Predicate Device Section */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Predicate Device Information (for 510(k))
          </h3>

          <div className="space-y-4">
            <div>
              <label
                htmlFor="predicate_device_name"
                className="block text-sm font-medium text-gray-700"
              >
                Predicate Device Name
              </label>
              <input
                type="text"
                id="predicate_device_name"
                name="predicate_device_name"
                value={formData.predicate_device_name}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                placeholder="e.g., HeartWatch 3000"
              />
            </div>

            <div>
              <label
                htmlFor="predicate_k_number"
                className="block text-sm font-medium text-gray-700"
              >
                Predicate K Number
              </label>
              <input
                type="text"
                id="predicate_k_number"
                name="predicate_k_number"
                value={formData.predicate_k_number}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                placeholder="e.g., K123456"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={generating || !formData.device_name}
            className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {generating ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Generating Submission...
              </>
            ) : (
              'Create & Generate Submission'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
