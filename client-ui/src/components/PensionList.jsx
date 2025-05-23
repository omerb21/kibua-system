import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getPensions, createPension, deletePension, getCommutations, createCommutation, deleteCommutation } from '../api/pensionApi';

function PensionList() {
  const { id: clientId } = useParams();
  const [pensions, setPensions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPensionForm, setShowPensionForm] = useState(false);
  const [showCommutationForm, setShowCommutationForm] = useState(false);
  const [selectedPension, setSelectedPension] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  
  const [pensionForm, setPensionForm] = useState({
    payer_name: '',
    start_date: ''
  });
  
  const [commutationForm, setCommutationForm] = useState({
    amount: '',
    date: '',
    full_or_partial: 'partial'
  });

  useEffect(() => {
    const fetchPensions = async () => {
      try {
        setLoading(true);
        // Note: In a real app, this endpoint would need to be implemented in the backend
        const response = await getPensions(clientId);
        
        // Load commutations for each pension
        const pensionsWithCommutations = await Promise.all(
          response.data.map(async (pension) => {
            try {
              const commutationsResponse = await getCommutations(pension.id);
              return {
                ...pension,
                commutations: commutationsResponse.data
              };
            } catch (err) {
              console.error(`Failed to load commutations for pension ${pension.id}`, err);
              return {
                ...pension,
                commutations: []
              };
            }
          })
        );
        
        setPensions(pensionsWithCommutations);
      } catch (err) {
        setError('שגיאה בטעינת רשימת הקצבאות');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPensions();
  }, [clientId]);

  const handlePensionChange = (e) => {
    const { name, value } = e.target;
    setPensionForm(prev => ({ ...prev, [name]: value }));
  };
  
  const handleCommutationChange = (e) => {
    const { name, value } = e.target;
    setCommutationForm(prev => ({ ...prev, [name]: value }));
  };

  const handlePensionSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      setError(null);
      
      // Note: In a real app, this endpoint would need to be implemented in the backend
      const response = await createPension(clientId, pensionForm);
      
      // Add the new pension to the list
      setPensions(prev => [...prev, { ...response.data, commutations: [] }]);
      
      // Reset form and hide it
      setPensionForm({
        payer_name: '',
        start_date: ''
      });
      setShowPensionForm(false);
    } catch (err) {
      setError('שגיאה בשמירת הקצבה');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };
  
  const handleCommutationSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setSubmitting(true);
      setError(null);
      
      // Convert amount to number
      const data = {
        ...commutationForm,
        amount: parseFloat(commutationForm.amount)
      };
      
      // Note: In a real app, this endpoint would need to be implemented in the backend
      const response = await createCommutation(selectedPension.id, data);
      
      // Update the commutations list for this pension
      setPensions(prev => 
        prev.map(pension => 
          pension.id === selectedPension.id
            ? { 
                ...pension, 
                commutations: [...pension.commutations, response.data] 
              }
            : pension
        )
      );
      
      // Reset form and hide it
      setCommutationForm({
        amount: '',
        date: '',
        full_or_partial: 'partial'
      });
      setShowCommutationForm(false);
      setSelectedPension(null);
    } catch (err) {
      setError('שגיאה בשמירת ההיוון');
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeletePension = async (pensionId) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק קצבה זו? כל ההיוונים המשויכים לקצבה זו יימחקו גם כן.')) {
      return;
    }
    
    try {
      // Note: In a real app, this endpoint would need to be implemented in the backend
      await deletePension(pensionId);
      
      // Remove the pension from the list
      setPensions(prev => prev.filter(pension => pension.id !== pensionId));
    } catch (err) {
      setError('שגיאה במחיקת הקצבה');
      console.error(err);
    }
  };
  
  const handleDeleteCommutation = async (pensionId, commutationId) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק היוון זה?')) {
      return;
    }
    
    try {
      // Note: In a real app, this endpoint would need to be implemented in the backend
      await deleteCommutation(commutationId);
      
      // Remove the commutation from the list
      setPensions(prev => 
        prev.map(pension => 
          pension.id === pensionId
            ? { 
                ...pension, 
                commutations: pension.commutations.filter(c => c.id !== commutationId) 
              }
            : pension
        )
      );
    } catch (err) {
      setError('שגיאה במחיקת ההיוון');
      console.error(err);
    }
  };
  
  const startAddCommutation = (pension) => {
    setSelectedPension(pension);
    setShowCommutationForm(true);
    setShowPensionForm(false);
  };

  if (loading) return <div className="text-center py-4">טוען נתונים...</div>;

  return (
    <div className="card mt-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold">קצבאות והיוונים</h3>
        <button 
          onClick={() => {
            setShowPensionForm(!showPensionForm);
            setShowCommutationForm(false);
          }} 
          className="btn"
        >
          {showPensionForm ? 'ביטול' : 'הוספת קצבה חדשה'}
        </button>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {showPensionForm && (
        <form onSubmit={handlePensionSubmit} className="mb-6 p-4 border rounded bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="payer_name">
                שם משלם הקצבה
              </label>
              <input
                type="text"
                id="payer_name"
                name="payer_name"
                value={pensionForm.payer_name}
                onChange={handlePensionChange}
                className="form-input"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="start_date">
                תאריך תחילת קצבה
              </label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                value={pensionForm.start_date}
                onChange={handlePensionChange}
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
              {submitting ? 'שומר...' : 'שמור קצבה'}
            </button>
          </div>
        </form>
      )}
      
      {showCommutationForm && selectedPension && (
        <form onSubmit={handleCommutationSubmit} className="mb-6 p-4 border rounded bg-gray-50">
          <h4 className="font-bold mb-4">הוסף היוון לקצבה: {selectedPension.payer_name}</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="amount">
                סכום היוון
              </label>
              <input
                type="number"
                id="amount"
                name="amount"
                value={commutationForm.amount}
                onChange={handleCommutationChange}
                className="form-input"
                required
                min="0"
                step="0.01"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="date">
                תאריך היוון
              </label>
              <input
                type="date"
                id="date"
                name="date"
                value={commutationForm.date}
                onChange={handleCommutationChange}
                className="form-input"
                required
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2" htmlFor="full_or_partial">
                סוג היוון
              </label>
              <select
                id="full_or_partial"
                name="full_or_partial"
                value={commutationForm.full_or_partial}
                onChange={handleCommutationChange}
                className="form-input"
                required
              >
                <option value="partial">חלקי</option>
                <option value="full">מלא</option>
              </select>
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => {
                setShowCommutationForm(false);
                setSelectedPension(null);
              }}
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
              {submitting ? 'שומר...' : 'שמור היוון'}
            </button>
          </div>
        </form>
      )}
      
      {pensions.length === 0 ? (
        <p className="text-gray-500 text-center py-4">לא נמצאו קצבאות ללקוח זה</p>
      ) : (
        <div>
          {pensions.map((pension) => (
            <div key={pension.id} className="mb-6 border rounded">
              <div className="flex justify-between items-center bg-gray-100 p-3 border-b">
                <div>
                  <h4 className="font-bold">{pension.payer_name}</h4>
                  <p className="text-sm">
                    תחילת קצבה: {new Date(pension.start_date).toLocaleDateString('he-IL')}
                  </p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => startAddCommutation(pension)}
                    className="btn-secondary ml-2 text-sm py-1"
                  >
                    הוסף היוון
                  </button>
                  <button
                    onClick={() => handleDeletePension(pension.id)}
                    className="text-red-600 hover:text-red-800"
                  >
                    מחק קצבה
                  </button>
                </div>
              </div>
              
              {pension.commutations && pension.commutations.length > 0 ? (
                <table className="min-w-full bg-white">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="py-2 px-4 text-right">סכום</th>
                      <th className="py-2 px-4 text-right">תאריך</th>
                      <th className="py-2 px-4 text-right">סוג</th>
                      <th className="py-2 px-4 text-right">פעולות</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pension.commutations.map((commutation) => (
                      <tr key={commutation.id} className="border-b hover:bg-gray-50">
                        <td className="py-2 px-4">{commutation.amount.toLocaleString()} ₪</td>
                        <td className="py-2 px-4">
                          {new Date(commutation.date).toLocaleDateString('he-IL')}
                        </td>
                        <td className="py-2 px-4">
                          {commutation.full_or_partial === 'full' ? 'מלא' : 'חלקי'}
                        </td>
                        <td className="py-2 px-4">
                          <button
                            onClick={() => handleDeleteCommutation(pension.id, commutation.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            מחק
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-500 text-center py-4">לא נמצאו היוונים לקצבה זו</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PensionList;
