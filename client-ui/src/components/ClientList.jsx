import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getClients, deleteClient } from '../api/clientApi';

function ClientList() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await getClients();
      setClients(response.data);
    } catch (err) {
      setError('שגיאה בטעינת רשימת הלקוחות');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);
  
  const handleDeleteClient = async (clientId) => {
    try {
      await deleteClient(clientId);
      setMessage('הלקוח נמחק בהצלחה');
      // Refresh the clients list
      fetchClients();
      setConfirmDelete(null);
      // Clear message after 3 seconds
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setError('שגיאה במחיקת הלקוח');
      console.error(err);
      // Clear error after 3 seconds
      setTimeout(() => setError(null), 3000);
    }
  };

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">רשימת לקוחות</h2>
        <Link to="/client/new" className="btn">לקוח חדש</Link>
      </div>
      
      {/* הודעת הצלחה */}
      {message && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4 text-right">
          {message}
        </div>
      )}
      
      {/* הודעת שגיאה */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 text-right">
          {error}
        </div>
      )}
      
      {clients.length === 0 ? (
        <p className="text-gray-500 text-center py-4">לא נמצאו לקוחות במערכת</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-100">
              <tr>
                <th className="py-2 px-4 text-right">שם</th>
                <th className="py-2 px-4 text-right">מספר זהות</th>
                <th className="py-2 px-4 text-right">תאריך לידה</th>
                <th className="py-2 px-4 text-right">טלפון</th>
                <th className="py-2 px-4 text-right">פעולות</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((client) => (
                <tr key={client.id} className="border-b hover:bg-gray-50">
                  <td className="py-2 px-4">{client.first_name} {client.last_name}</td>
                  <td className="py-2 px-4">{client.tz}</td>
                  <td className="py-2 px-4">{client.birth_date}</td>
                  <td className="py-2 px-4">{client.phone}</td>
                  <td className="py-2 px-4">
                    <div className="flex space-x-2">
                      <Link 
                        to={`/client/${client.id}`} 
                        className="text-blue-600 hover:underline ml-2"
                      >
                        פרטים
                      </Link>
                      <Link 
                        to={`/client/${client.id}/summary`}
                        className="text-green-600 hover:underline ml-2"
                      >
                        סיכום
                      </Link>

                      <Link 
                        to={`/client/${client.id}/edit`}
                        className="text-orange-600 hover:underline ml-2"
                      >
                        עריכה
                      </Link>
                      <button 
                        onClick={() => setConfirmDelete(client.id)}
                        className="text-red-600 hover:underline"
                      >
                        מחיקה
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Confirmation Dialog for Deleting Client */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full">
            <h3 className="text-xl font-bold mb-4 text-right">אישור מחיקה</h3>
            <p className="mb-4 text-right">האם אתה בטוח שברצונך למחוק את הלקוח וכל הנתונים הקשורים אליו? פעולה זו אינה ניתנת לשחזור.</p>
            <div className="flex justify-end space-x-2">
              <button 
                onClick={() => setConfirmDelete(null)} 
                className="btn-secondary ml-2"
              >
                ביטול
              </button>
              <button 
                onClick={() => handleDeleteClient(confirmDelete)} 
                className="btn-danger"
              >
                מחק
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ClientList;
