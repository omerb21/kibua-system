import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import ClientForm from '../components/ClientForm';
import GrantList from '../components/GrantList';
import PensionList from '../components/PensionList';
import { getClient } from '../api/clientApi';

function ClientPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNewClient = id === 'new';
  
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(!isNewClient);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchClient = async () => {
      if (isNewClient) return;
      
      try {
        setLoading(true);
        const response = await getClient(id);
        setClient(response.data);
      } catch (err) {
        setError('שגיאה בטעינת פרטי הלקוח');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchClient();
  }, [id, isNewClient]);

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center">
          <button onClick={() => navigate(-1)} className="text-blue-600 hover:underline flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 ml-1">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
            </svg>
            חזרה
          </button>
        </div>
        
        <h1 className="text-3xl font-bold mt-2">
          {isNewClient ? 'לקוח חדש' : `${client?.first_name} ${client?.last_name}`}
        </h1>
        
        {!isNewClient && (
          <div className="flex mt-4 space-x-4">
            <Link to={`/client/${id}/summary`} className="btn-secondary ml-2">
              סיכום קיבוע זכויות
            </Link>

          </div>
        )}
      </div>
      
      <ClientForm />
      
      {!isNewClient && (
        <>
          <GrantList />
          <PensionList />
        </>
      )}
    </div>
  );
}

export default ClientPage;
