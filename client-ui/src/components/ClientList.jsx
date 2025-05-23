import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getClients } from '../api/clientApi';

function ClientList() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
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

    fetchClients();
  }, []);

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">רשימת לקוחות</h2>
        <Link to="/client/new" className="btn">לקוח חדש</Link>
      </div>
      
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
                        to={`/client/${client.id}/documents`}
                        className="text-purple-600 hover:underline"
                      >
                        מסמכים
                      </Link>
                    </div>
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

export default ClientList;
