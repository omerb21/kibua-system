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
  const [recalculating, setRecalculating] = useState(false);
  const [message, setMessage] = useState(null);

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
  
  // פונקציה לחישוב מחדש של המענקים
  const handleRecalculation = async () => {
    try {
      setRecalculating(true);
      setMessage(null);
      setError(null);
      
      // קריאה ל-API עם דגל חישוב מחדש
      const summaryResponse = await calculateExemptionSummary(clientId, true);
      setSummary(summaryResponse.data);
      
      // הצגת הודעת הצלחה
      setMessage('החישוב עודכן בהצלחה. הערכים המעודכנים מוצגים כעת.');
    } catch (err) {
      setError('שגיאה בחישוב מחדש של הנתונים');
      console.error(err);
    } finally {
      setRecalculating(false);
    }
  };

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;
  if (error) return <div className="text-red-500 text-center py-4">{error}</div>;
  if (!client || !summary) return <div className="text-center py-4">לא נמצאו נתונים</div>;

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">סיכום קיבוע זכויות</h2>
        <button 
          onClick={handleRecalculation}
          disabled={recalculating}
          className="btn bg-indigo-600 hover:bg-indigo-700 text-white"
        >
          {recalculating ? 'מחשב מחדש...' : 'חשב מחדש'}
        </button>
      </div>
      
      {message && (
        <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded">
          {message}
        </div>
      )}
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      
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
              {summary.client_info && summary.client_info.eligibility_date && 
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
                  {summary.exempt_cap.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">סך מענקים נומינליים</td>
                <td className="py-3 px-4 text-left">
                  {summary.grants_nominal.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">סך מענקים מוצמדים</td>
                <td className="py-3 px-4 text-left">
                  {summary.grants_indexed.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">סך פגיעה בפטור</td>
                <td className="py-3 px-4 text-left">
                  {summary.grants_impact.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">סך היוונים</td>
                <td className="py-3 px-4 text-left">
                  {summary.commutations_total.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">יתרת תקרה זמינה</td>
                <td className="py-3 px-4 text-left">
                  {summary.remaining_cap.toLocaleString()} ₪
                </td>
              </tr>
              <tr className="border-b">
                <td className="py-3 px-4 bg-blue-50 font-medium">תקרת קצבה מזכה</td>
                <td className="py-3 px-4 text-left">
                  {summary.monthly_cap.toLocaleString()} ₪
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 bg-green-100 font-medium text-lg">קצבה פטורה מחושבת</td>
                <td className="py-3 px-4 text-left font-bold text-lg">
                  {summary.pension_exempt.toLocaleString()} ₪ ({summary.pension_rate}%)
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
            <p className="font-medium">{summary.details && summary.details.grants_count || 0}</p>
          </div>
          <div>
            <p className="text-gray-600">מספר היוונים שנלקחו בחשבון:</p>
            <p className="font-medium">{summary.details && summary.details.commutations_count || 0}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SummaryView;
