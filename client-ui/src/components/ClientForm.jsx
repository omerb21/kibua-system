import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getClient, createClient } from '../api/clientApi';

function ClientForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isNewClient = id === 'new';
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    tz: '',
    birth_date: '',
    gender: 'male', // Default to male
    phone: '',
    address: ''
  });
  
  const [loading, setLoading] = useState(!isNewClient);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchClient = async () => {
      if (isNewClient) return;
      
      try {
        setLoading(true);
        const response = await getClient(id);
        // Format date from ISO to YYYY-MM-DD for input field
        const client = response.data;
        if (client.birth_date) {
          client.birth_date = client.birth_date.split('T')[0];
        }
        setFormData(client);
      } catch (err) {
        setError('שגיאה בטעינת פרטי הלקוח');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchClient();
  }, [id, isNewClient]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      setError(null);
      
      if (isNewClient) {
        const response = await createClient(formData);
        // Navigate to the new client's page
        navigate(`/client/${response.data.id}`);
      } else {
        // TODO: Implement update client functionality in the backend
        // await updateClient(id, formData);
        alert('עדכון לקוח קיים אינו נתמך עדיין');
      }
    } catch (err) {
      setError('שגיאה בשמירת הנתונים');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-6">
        {isNewClient ? 'לקוח חדש' : 'עריכת פרטי לקוח'}
      </h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-gray-700 mb-2" htmlFor="first_name">
              שם פרטי
            </label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-700 mb-2" htmlFor="last_name">
              שם משפחה
            </label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-700 mb-2" htmlFor="tz">
              מספר זהות
            </label>
            <input
              type="text"
              id="tz"
              name="tz"
              value={formData.tz}
              onChange={handleChange}
              className="form-input"
              required
              pattern="[0-9]{9}"
              title="נדרשים 9 ספרות"
            />
          </div>
          
          <div>
            <label className="block text-gray-700 mb-2" htmlFor="birth_date">
              תאריך לידה
            </label>
            <input
              type="date"
              id="birth_date"
              name="birth_date"
              value={formData.birth_date}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-700 mb-2" htmlFor="gender">
              מגדר
            </label>
            <select
              id="gender"
              name="gender"
              value={formData.gender}
              onChange={handleChange}
              className="form-input"
              required
            >
              <option value="male">זכר</option>
              <option value="female">נקבה</option>
            </select>
          </div>
          
          <div>
            <label className="block text-gray-700 mb-2" htmlFor="phone">
              טלפון
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="form-input"
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-gray-700 mb-2" htmlFor="address">
              כתובת
            </label>
            <input
              type="text"
              id="address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              className="form-input"
            />
          </div>
        </div>
        
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn-secondary ml-2"
            disabled={submitting}
          >
            ביטול
          </button>
          <button
            type="submit"
            className="btn"
            disabled={submitting}
          >
            {submitting ? 'שומר...' : 'שמור'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ClientForm;
