import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { fillForm161d } from '../api/calcApi';

function DocumentPanel() {
  const { id: clientId } = useParams();
  const [loading, setLoading] = useState(false);
  const [generatedPdf, setGeneratedPdf] = useState(null);
  const [error, setError] = useState(null);

  const handleGeneratePdf = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fillForm161d(clientId);
      setGeneratedPdf(response.data);
    } catch (err) {
      setError('שגיאה בהפקת הטופס');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-bold mb-6">הפקת מסמכים</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="mb-6 p-6 bg-gray-50 rounded-lg border">
        <h3 className="text-lg font-semibold mb-4">טופס 161ד - הודעת קיבוע זכויות</h3>
        <p className="mb-4">
          הפקת טופס מלא עם כל נתוני הלקוח וחישובי הפטור לקצבה.
        </p>
        
        {generatedPdf ? (
          <div className="flex flex-col space-y-4">
            <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
              <p className="font-medium">הטופס נוצר בהצלחה!</p>
              <p className="text-sm">ניתן להוריד את הטופס בקישור למטה.</p>
            </div>
            
            <a 
              href={generatedPdf.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn flex items-center justify-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              הורד טופס 161ד
            </a>
          </div>
        ) : (
          <button
            onClick={handleGeneratePdf}
            disabled={loading}
            className="btn flex items-center justify-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                מפיק טופס...
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                הפק טופס 161ד
              </>
            )}
          </button>
        )}
      </div>
      
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="font-semibold mb-2">הערה חשובה</h4>
        <p className="text-sm">
          יש לוודא שכל הנתונים של הלקוח מעודכנים לפני הפקת הטופס. אנא בדוק את פרטי הלקוח, המענקים והקצבאות.
        </p>
      </div>
    </div>
  );
}

export default DocumentPanel;
