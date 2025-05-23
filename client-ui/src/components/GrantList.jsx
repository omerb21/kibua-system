import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getGrants, createGrant, deleteGrant } from '../api/grantApi';

function GrantList() {
  const { id: clientId } = useParams();
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const [formData, setFormData] = useState({
    employer_name: '',
    work_start_date: '',
    work_end_date: '',
    grant_amount: '',
    grant_date: ''
  });

  useEffect(() => {
    const fetchGrants = async () => {
      try {
        setLoading(true);
        // Note: In a real app, this endpoint would need to be implemented in the backend
        const response = await getGrants(clientId);
        setGrants(response.data);
      } catch (err) {
        setError('שגיאה בטעינת רשימת המענקים');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchGrants();
  }, [clientId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      setError(null);
      
      // Convert amount to number
      const data = {
        ...formData,
        grant_amount: parseFloat(formData.grant_amount)
      };
      
      // Note: In a real app, this endpoint would need to be implemented in the backend
      const response = await createGrant(clientId, data);
      
      // Add the new grant to the list
      setGrants(prev => [...prev, response.data]);
      
      // Reset form and hide it
      setFormData({
        employer_name: '',
        work_start_date: '',
        work_end_date: '',
        grant_amount: '',
        grant_date: ''
      });
      setShowForm(false);
    } catch (err) {
      setError('שגיאה בשמירת המענק');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (grantId) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק מענק זה?')) {
      return;
    }
    
    try {
      // Note: In a real app, this endpoint would need to be implemented in the backend
      await deleteGrant(grantId);
      
      // Remove the grant from the list
      setGrants(prev => prev.filter(grant => grant.id !== grantId));
    } catch (err) {
      setError('שגיאה במחיקת המענק');
      console.error(err);
    }
  };

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;

  return (
    <div className="card mt-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold">מענקים פטורים</h3>
        <button 
          onClick={() => setShowForm(!showForm)} 
          className="btn"
        >
          {showForm ? 'ביטול' : 'הוספת מענק חדש'}
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 p-4 border rounded bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="employer_name">
                שם מעסיק
              </label>
              <input
                type="text"
                id="employer_name"
                name="employer_name"
                value={formData.employer_name}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="work_start_date">
                תאריך תחילת עבודה
              </label>
              <input
                type="date"
                id="work_start_date"
                name="work_start_date"
                value={formData.work_start_date}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="work_end_date">
                תאריך סיום עבודה
              </label>
              <input
                type="date"
                id="work_end_date"
                name="work_end_date"
                value={formData.work_end_date}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="grant_amount">
                סכום מענק
              </label>
              <input
                type="number"
                id="grant_amount"
                name="grant_amount"
                value={formData.grant_amount}
                onChange={handleChange}
                className="form-input"
                required
                min="0"
                step="0.01"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="grant_date">
                תאריך קבלת מענק
              </label>
              <input
                type="date"
                id="grant_date"
                name="grant_date"
                value={formData.grant_date}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
          </div>
          
          <div className="flex justify-end">
            <button
              type="submit"
              className="btn"
              disabled={submitting}
            >
              {submitting ? 'שומר...' : 'שמור מענק'}
            </button>
          </div>
        </form>
      )}
      
      {grants.length === 0 ? (
        <p className="text-gray-500 text-center py-4">לא נמצאו מענקים ללקוח זה</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-100">
              <tr>
                <th className="py-2 px-4 text-right">מעסיק</th>
                <th className="py-2 px-4 text-right">תקופת עבודה</th>
                <th className="py-2 px-4 text-right">סכום מענק</th>
                <th className="py-2 px-4 text-right">תאריך קבלה</th>
                <th className="py-2 px-4 text-right">פעולות</th>
              </tr>
            </thead>
            <tbody>
              {grants.map((grant) => (
                <tr key={grant.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-4">{grant.employer_name}</td>
                  <td className="py-2 px-4">
                    {new Date(grant.work_start_date).toLocaleDateString('he-IL')} - 
                    {new Date(grant.work_end_date).toLocaleDateString('he-IL')}
                  </td>
                  <td className="py-2 px-4">{grant.grant_amount.toLocaleString()} ₪</td>
                  <td className="py-2 px-4">
                    {new Date(grant.grant_date).toLocaleDateString('he-IL')}
                  </td>
                  <td className="py-2 px-4">
                    <button
                      onClick={() => handleDelete(grant.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      מחק
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default GrantList;
