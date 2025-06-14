import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import SummaryView from '../components/SummaryView';
import { createPackage } from '../api/clientApi';
import { getClient } from '../api/clientApi';

function SummaryPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pkgInfo, setPkgInfo] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    const fetchClient = async () => {
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
  }, [id]);

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
          סיכום קיבוע זכויות - {client?.first_name} {client?.last_name}
        </h1>
        
        <div className="flex mt-4 space-x-4">
          <Link to={`/client/${id}`} className="btn-secondary ml-2">
            פרטי לקוח
          </Link>
          <button
            onClick={async () => {
              try {
                setGenerating(true);
                const res = await createPackage(id);
                setPkgInfo(res.data);
                alert(`המסמכים נשמרו ב-${res.data.folder}`);
              } catch (err) {
                console.error(err);
                alert('אירעה שגיאה בהפקת החבילה');
              } finally {
                setGenerating(false);
              }
            }}
            className="btn bg-indigo-600 hover:bg-indigo-700 text-white ml-2"
          >
            {generating ? 'מפיק...' : 'הפקת טפסים'}
          </button>
        </div>
      </div>

      {pkgInfo && (
        <div className="mt-4 p-4 border rounded bg-blue-50">
          <p className="font-semibold mb-2">קבצים שנוצרו:</p>
          <ul className="list-disc ps-6">
            {pkgInfo.files.map((f) => (
              <li key={f}>
                <a href={`/${pkgInfo.folder}/${f}`} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                  {f}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <SummaryView />
    </div>
  );
}

export default SummaryPage;
