import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { calculateExemptionSummary } from '../api/calcApi';
import { getClient } from '../api/clientApi';

function SummaryView() {
  const { id: clientId } = useParams();
  const [client, setClient] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Get client details
        const clientResponse = await getClient(clientId);
        setClient(clientResponse.data);
        
        // Get exemption summary
        const summaryResponse = await calculateExemptionSummary(clientId);
        setSummary(summaryResponse.data);
      } catch (err) {
        setError('שגיאה בטעינת נתוני הסיכום');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [clientId]);

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;
  if (!client || !summary) return <div className="text-center py-4">לא נמצאו נתונים</div>;

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-6">סיכום קיבוע זכויות</h2>
      
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
        <h3 className="text-lg font-semibold mb-2">פרטי לקוח</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-gray-600">שם מלא:</p>
            <p className="font-medium">{client.first_name} {client.last_name}</p>
          </div>
          <div>
            <p className="text-gray-600">מספר זהות:</p>
            <p className="font-medium">{client.tz}</p>
          </div>
          <div>
            <p className="text-gray-600">תאריך לידה:</p>
            <p className="font-medium">
              {client.birth_date && new Date(client.birth_date).toLocaleDateString('he-IL')}
            </p>
          </div>
          <div>
            <p className="text-gray-600">תאריך זכאות:</p>
            <p className="font-medium">
              {summary.client_info.eligibility_date && 
                new Date(summary.client_info.eligibility_date).toLocaleDateString('he-IL')}
            </p>
          </div>
        </div>
      </div>
      
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">סיכום חישובים</h3>
        <div className="overflow-hidden rounded-lg border">
          <table className="min-w-full bg-white">
            <tbody>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">תקרת הון פטורה לשנת הזכאות</td>
                <td className="py-3 px-4 text-left">
                  {summary.exemption_summary.exemption_cap_for_year.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">סך פגיעה ממענקים פטורים</td>
                <td className="py-3 px-4 text-left">
                  {summary.exemption_summary.total_grant_impact.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">יתרת תקרה זמינה</td>
                <td className="py-3 px-4 text-left">
                  {summary.exemption_summary.available_exemption_cap.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">סך פגיעה מהיוונים</td>
                <td className="py-3 px-4 text-left">
                  {summary.exemption_summary.total_commutation_impact.toLocaleString()} ₪
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 bg-green-100 font-medium text-lg">סכום פטור סופי לקצבה</td>
                <td className="py-3 px-4 text-left font-bold text-lg">
                  {summary.exemption_summary.final_exempt_amount.toLocaleString()} ₪
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-2">פרטים נוספים</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg border">
          <div>
            <p className="text-gray-600">מספר מענקים שנלקחו בחשבון:</p>
            <p className="font-medium">{summary.details.grants_count}</p>
          </div>
          <div>
            <p className="text-gray-600">מספר היוונים שנלקחו בחשבון:</p>
            <p className="font-medium">{summary.details.commutations_count}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SummaryView;
